from __future__ import annotations

import html
import secrets
from dataclasses import dataclass
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
import urllib.parse

from digest.admin.service import AdminConfig, AdminService


@dataclass(slots=True)
class SessionData:
    username: str
    csrf: str


def run_admin_server(
    *,
    host: str,
    port: int,
    service: AdminService,
    admin_user: str,
    admin_password: str,
) -> None:
    server = create_admin_server(
        host=host,
        port=port,
        service=service,
        admin_user=admin_user,
        admin_password=admin_password,
    )
    server.serve_forever()


def create_admin_server(
    *,
    host: str,
    port: int,
    service: AdminService,
    admin_user: str,
    admin_password: str,
) -> ThreadingHTTPServer:
    sessions: dict[str, SessionData] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self._dispatch("GET")

        def do_POST(self):  # noqa: N802
            self._dispatch("POST")

        def _dispatch(self, method: str) -> None:
            path, _, query = self.path.partition("?")
            params = urllib.parse.parse_qs(query)
            if path == "/admin/login" and method == "GET":
                return self._render_login("")
            if path == "/admin/login" and method == "POST":
                form = self._form_data()
                user = form.get("username", "")
                pwd = form.get("password", "")
                if user == admin_user and pwd == admin_password:
                    sid = secrets.token_urlsafe(24)
                    sessions[sid] = SessionData(username=user, csrf=secrets.token_urlsafe(24))
                    self.send_response(303)
                    ck = cookies.SimpleCookie()
                    ck["admin_session"] = sid
                    ck["admin_session"]["httponly"] = True
                    ck["admin_session"]["samesite"] = "Lax"
                    ck["admin_session"]["path"] = "/"
                    self.send_header("Set-Cookie", ck.output(header="").strip())
                    self.send_header("Location", "/admin/runs")
                    self.end_headers()
                    return
                return self._render_login("Invalid credentials")

            session = self._session()
            if path.startswith("/admin") and not session:
                self.send_response(303)
                self.send_header("Location", "/admin/login")
                self.end_headers()
                return

            if path == "/admin" and method == "GET":
                return self._redirect("/admin/runs")
            if path == "/admin/logout" and method == "POST":
                form = self._form_data()
                if not self._csrf_ok(session, form):
                    return self._forbidden("Invalid CSRF token")
                sid = self._session_id()
                if sid:
                    sessions.pop(sid, None)
                self.send_response(303)
                ck = cookies.SimpleCookie()
                ck["admin_session"] = ""
                ck["admin_session"]["path"] = "/"
                ck["admin_session"]["max-age"] = 0
                self.send_header("Set-Cookie", ck.output(header="").strip())
                self.send_header("Location", "/admin/login")
                self.end_headers()
                return

            if path == "/admin/sources" and method == "GET":
                return self._render_sources(session)
            if path == "/admin/sources/add" and method == "POST":
                return self._mutate_source(session, add=True)
            if path == "/admin/sources/remove" and method == "POST":
                return self._mutate_source(session, add=False)

            if path == "/admin/bot" and method == "GET":
                return self._render_bot(session)
            if path == "/admin/bot/start" and method == "POST":
                return self._bot_action(session, "start")
            if path == "/admin/bot/stop" and method == "POST":
                return self._bot_action(session, "stop")
            if path == "/admin/bot/restart" and method == "POST":
                return self._bot_action(session, "restart")

            if path == "/admin/runs" and method == "GET":
                return self._render_runs(session)
            if path == "/admin/runs/trigger" and method == "POST":
                return self._run_trigger(session)

            if path == "/admin/logs" and method == "GET":
                return self._render_logs(session, params)

            if path == "/admin/outputs" and method == "GET":
                return self._render_outputs(session)

            if path == "/admin/feedback" and method == "GET":
                return self._render_feedback(session)
            if path == "/admin/feedback/add" and method == "POST":
                return self._feedback_add(session)

            self.send_response(404)
            self.end_headers()

        def _layout(self, title: str, body: str, session: SessionData | None) -> None:
            nav = ""
            if session:
                nav = (
                    '<nav>'
                    '<a href="/admin/runs">Runs</a> | '
                    '<a href="/admin/sources">Sources</a> | '
                    '<a href="/admin/bot">Bot</a> | '
                    '<a href="/admin/logs">Logs</a> | '
                    '<a href="/admin/outputs">Outputs</a> | '
                    '<a href="/admin/feedback">Feedback</a>'
                    '</nav><hr/>'
                )
            html_doc = f"""
<!doctype html>
<html><head><meta charset='utf-8'><title>{html.escape(title)}</title></head>
<body>
<h1>{html.escape(title)}</h1>
{nav}
{body}
</body></html>
"""
            raw = html_doc.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _render_login(self, error: str) -> None:
            msg = f"<p style='color:red'>{html.escape(error)}</p>" if error else ""
            body = (
                f"{msg}<form method='post' action='/admin/login'>"
                "<label>Username <input name='username'/></label><br/>"
                "<label>Password <input name='password' type='password'/></label><br/>"
                "<button type='submit'>Login</button>"
                "</form>"
            )
            self._layout("Admin Login", body, None)

        def _render_sources(self, session: SessionData) -> None:
            rows = service.list_sources()
            items = []
            for st in sorted(rows):
                vals = "".join(f"<li>{html.escape(v)}</li>" for v in rows[st][:100])
                items.append(f"<h3>{html.escape(st)} ({len(rows[st])})</h3><ul>{vals}</ul>")
            body = (
                self._logout_form(session)
                + "".join(items)
                + self._source_form(session, add=True)
                + self._source_form(session, add=False)
            )
            self._layout("Admin Sources", body, session)

        def _source_form(self, session: SessionData, *, add: bool) -> str:
            action = "add" if add else "remove"
            return (
                f"<h3>{action.title()} Source</h3>"
                f"<form method='post' action='/admin/sources/{action}'>"
                f"<input type='hidden' name='csrf' value='{html.escape(session.csrf)}'/>"
                "<label>Type <input name='source_type'/></label><br/>"
                "<label>Value <input name='value' size='80'/></label><br/>"
                f"<button type='submit'>{action.title()}</button>"
                "</form>"
            )

        def _mutate_source(self, session: SessionData, *, add: bool) -> None:
            form = self._form_data()
            if not self._csrf_ok(session, form):
                return self._forbidden("Invalid CSRF token")
            st = form.get("source_type", "")
            value = form.get("value", "")
            if add:
                ok, canonical = service.add_source(session.username, st, value)
                msg = f"Added: {canonical}" if ok else f"Already present: {canonical}"
            else:
                ok, canonical = service.remove_source(session.username, st, value)
                msg = f"Removed: {canonical}" if ok else f"Not found: {canonical}"
            self._redirect(f"/admin/sources?msg={urllib.parse.quote(msg)}")

        def _render_bot(self, session: SessionData) -> None:
            status = service.bot_status()
            body = (
                self._logout_form(session)
                + f"<p>State: {html.escape(status['state'])}, PID: {html.escape(status['pid'])}, Started: {html.escape(status['started_at'])}</p>"
                + self._action_form(session, "/admin/bot/start", "Start")
                + self._action_form(session, "/admin/bot/stop", "Stop")
                + self._action_form(session, "/admin/bot/restart", "Restart")
            )
            self._layout("Admin Bot", body, session)

        def _bot_action(self, session: SessionData, action: str) -> None:
            form = self._form_data()
            if not self._csrf_ok(session, form):
                return self._forbidden("Invalid CSRF token")
            if action == "start":
                ok, msg = service.bot_start(session.username)
            elif action == "stop":
                ok, msg = service.bot_stop(session.username)
            else:
                ok, msg = service.bot_restart(session.username)
            _ = ok
            self._redirect(f"/admin/bot?msg={urllib.parse.quote(msg)}")

        def _render_runs(self, session: SessionData) -> None:
            runs = service.runs(limit=200)
            rows = "".join(
                f"<tr><td>{html.escape(r.run_id)}</td><td>{html.escape(r.status)}</td><td>{html.escape(r.started_at)}</td><td>{html.escape(r.window_start)}</td><td>{html.escape(r.window_end)}</td></tr>"
                for r in runs
            )
            body = (
                self._logout_form(session)
                + self._action_form(session, "/admin/runs/trigger", "Run now")
                + "<table border='1'><tr><th>run_id</th><th>status</th><th>started_at</th><th>window_start</th><th>window_end</th></tr>"
                + rows
                + "</table>"
            )
            self._layout("Admin Runs", body, session)

        def _run_trigger(self, session: SessionData) -> None:
            form = self._form_data()
            if not self._csrf_ok(session, form):
                return self._forbidden("Invalid CSRF token")
            ok, msg = service.run_now(session.username)
            _ = ok
            self._redirect(f"/admin/runs?msg={urllib.parse.quote(msg)}")

        def _render_logs(self, session: SessionData, params: dict[str, list[str]]) -> None:
            run_id = (params.get("run_id") or [""])[0]
            stage = (params.get("stage") or [""])[0]
            level = (params.get("level") or [""])[0]
            rows = service.logs(run_id=run_id, stage=stage, level=level, limit=300)
            body_rows = "".join(f"<pre>{html.escape(str(r))}</pre>" for r in rows)
            body = (
                self._logout_form(session)
                + "<form method='get' action='/admin/logs'>"
                f"<label>run_id <input name='run_id' value='{html.escape(run_id)}'/></label> "
                f"<label>stage <input name='stage' value='{html.escape(stage)}'/></label> "
                f"<label>level <input name='level' value='{html.escape(level)}'/></label> "
                "<button type='submit'>Filter</button></form>"
                + body_rows
            )
            self._layout("Admin Logs", body, session)

        def _render_outputs(self, session: SessionData) -> None:
            out = service.outputs()
            body = (
                self._logout_form(session)
                + f"<h3>Obsidian latest</h3><p>{html.escape(out['obsidian_latest'])}</p><pre>{html.escape(out['obsidian_preview'])}</pre>"
                + f"<h3>Telegram preview</h3><pre>{html.escape(out['telegram_preview'])}</pre>"
            )
            self._layout("Admin Outputs", body, session)

        def _render_feedback(self, session: SessionData) -> None:
            rows = service.feedback(limit=200)
            summary = service.feedback_summary()
            audit = service.audit(limit=100)
            body_rows = "".join(
                f"<tr><td>{r[0]}</td><td>{html.escape(r[1])}</td><td>{html.escape(r[2])}</td><td>{r[3]}</td><td>{html.escape(r[4])}</td><td>{html.escape(r[5])}</td><td>{html.escape(r[6])}</td></tr>"
                for r in rows
            )
            summary_text = ", ".join(f"{rating}:{count}" for rating, count in summary)
            audit_rows = "".join(
                f"<tr><td>{a[0]}</td><td>{html.escape(a[1])}</td><td>{html.escape(a[2])}</td><td>{html.escape(a[3])}</td><td>{html.escape(a[4])}</td><td>{html.escape(a[5])}</td></tr>"
                for a in audit
            )
            body = (
                self._logout_form(session)
                + f"<p>Rating summary: {html.escape(summary_text)}</p>"
                + "<h3>Add Feedback</h3>"
                + "<form method='post' action='/admin/feedback/add'>"
                + f"<input type='hidden' name='csrf' value='{html.escape(session.csrf)}'/>"
                + "<label>run_id <input name='run_id'/></label><br/>"
                + "<label>item_id <input name='item_id'/></label><br/>"
                + "<label>rating <input name='rating' type='number' min='1' max='5'/></label><br/>"
                + "<label>label <input name='label'/></label><br/>"
                + "<label>comment <input name='comment' size='80'/></label><br/>"
                + "<button type='submit'>Save feedback</button></form>"
                + "<h3>Feedback</h3><table border='1'><tr><th>id</th><th>run_id</th><th>item_id</th><th>rating</th><th>label</th><th>comment</th><th>created_at</th></tr>"
                + body_rows
                + "</table>"
                + "<h3>Admin Audit</h3><table border='1'><tr><th>id</th><th>actor</th><th>action</th><th>target</th><th>details</th><th>created_at</th></tr>"
                + audit_rows
                + "</table>"
            )
            self._layout("Admin Feedback", body, session)

        def _feedback_add(self, session: SessionData) -> None:
            form = self._form_data()
            if not self._csrf_ok(session, form):
                return self._forbidden("Invalid CSRF token")
            run_id = form.get("run_id", "")
            item_id = form.get("item_id", "")
            rating = int(form.get("rating", "0") or "0")
            label = form.get("label", "")
            comment = form.get("comment", "")
            if not run_id or not item_id or rating < 1 or rating > 5:
                return self._forbidden("Invalid feedback payload")
            service.add_feedback(session.username, run_id=run_id, item_id=item_id, rating=rating, label=label, comment=comment)
            self._redirect("/admin/feedback")

        def _redirect(self, location: str) -> None:
            self.send_response(303)
            self.send_header("Location", location)
            self.end_headers()

        def _forbidden(self, message: str) -> None:
            raw = message.encode("utf-8")
            self.send_response(403)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _logout_form(self, session: SessionData) -> str:
            return (
                "<form method='post' action='/admin/logout'>"
                f"<input type='hidden' name='csrf' value='{html.escape(session.csrf)}'/>"
                "<button type='submit'>Logout</button></form>"
            )

        def _action_form(self, session: SessionData, action: str, label: str) -> str:
            return (
                f"<form method='post' action='{html.escape(action)}'>"
                f"<input type='hidden' name='csrf' value='{html.escape(session.csrf)}'/>"
                f"<button type='submit'>{html.escape(label)}</button></form>"
            )

        def _session_id(self) -> str:
            header = self.headers.get("Cookie", "")
            ck = cookies.SimpleCookie()
            ck.load(header)
            morsel = ck.get("admin_session")
            return morsel.value if morsel else ""

        def _session(self) -> SessionData | None:
            sid = self._session_id()
            return sessions.get(sid)

        def _csrf_ok(self, session: SessionData, form: dict[str, str]) -> bool:
            return form.get("csrf", "") == session.csrf

        def _form_data(self) -> dict[str, str]:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(max(0, length)).decode("utf-8")
            parsed = urllib.parse.parse_qs(raw)
            return {k: (v[0] if v else "") for k, v in parsed.items()}

        def log_message(self, format: str, *args):  # noqa: A003
            return

    return ThreadingHTTPServer((host, port), Handler)


def make_admin_service(
    *,
    sources_path: str,
    profile_path: str,
    db_path: str,
    overlay_path: str,
    run_lock_path: str,
    bot_pid_path: str,
    bot_log_path: str,
) -> AdminService:
    cfg = AdminConfig(
        sources_path=sources_path,
        profile_path=profile_path,
        db_path=db_path,
        overlay_path=overlay_path,
        run_lock_path=run_lock_path,
        bot_pid_path=bot_pid_path,
        bot_log_path=bot_log_path,
    )
    return AdminService(cfg)
