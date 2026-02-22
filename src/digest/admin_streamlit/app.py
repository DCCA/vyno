from __future__ import annotations

import json
from pathlib import Path

from digest.admin.service import AdminConfig, AdminService
from digest.admin_streamlit.config import load_streamlit_admin_config
from digest.ops.source_registry import canonicalize_source_value, supported_source_types

_SOURCE_META = {
    "rss": {
        "label": "RSS Feed",
        "hint": "Use a full http/https feed URL.",
        "placeholder": "https://openai.com/news/rss.xml",
    },
    "youtube_channel": {
        "label": "YouTube Channel ID",
        "hint": "Use channel IDs like UC_x5XG1OV2P6uZZ5FSM9Ttw.",
        "placeholder": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
    },
    "youtube_query": {
        "label": "YouTube Query",
        "hint": "Use short topic queries (spaces are normalized).",
        "placeholder": "ai agents",
    },
    "github_repo": {
        "label": "GitHub Repository",
        "hint": "owner/repo or full URL.",
        "placeholder": "vercel/next.js",
    },
    "github_topic": {
        "label": "GitHub Topic",
        "hint": "Single topic token.",
        "placeholder": "ai-agents",
    },
    "github_query": {
        "label": "GitHub Search Query",
        "hint": "GitHub search syntax is supported.",
        "placeholder": "topic:ai language:python stars:>500",
    },
    "github_org": {
        "label": "GitHub Organization",
        "hint": "org login or GitHub org URL. Tracks releases + repo updates.",
        "placeholder": "https://github.com/vercel-labs",
    },
}


def _inject_css(st) -> None:
    st.markdown(
        """
<style>
.block-container {
  max-width: 1240px;
  padding-top: 1.2rem;
}
.ui-kicker {
  display: inline-block;
  font-size: 0.75rem;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: #14b8a6;
  background: rgba(20, 184, 166, 0.14);
  border-radius: 8px;
  padding: 0.2rem 0.5rem;
  font-weight: 700;
}
.ui-title {
  margin: 0.35rem 0 0.2rem 0;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: inherit;
}
.ui-sub {
  color: inherit;
  opacity: 0.82;
  margin: 0 0 0.8rem 0;
}
</style>
""",
        unsafe_allow_html=True,
    )


def _get_service(st, cfg) -> AdminService:
    @st.cache_resource
    def _cached_service(
        sources_path: str,
        profile_path: str,
        db_path: str,
        overlay_path: str,
        run_lock_path: str,
        bot_pid_path: str,
        bot_log_path: str,
    ) -> AdminService:
        return AdminService(
            AdminConfig(
                sources_path=sources_path,
                profile_path=profile_path,
                db_path=db_path,
                overlay_path=overlay_path,
                run_lock_path=run_lock_path,
                bot_pid_path=bot_pid_path,
                bot_log_path=bot_log_path,
            )
        )

    return _cached_service(
        cfg.sources_path,
        cfg.profile_path,
        cfg.db_path,
        cfg.overlay_path,
        cfg.run_lock_path,
        cfg.bot_pid_path,
        cfg.bot_log_path,
    )


def _render_overview(st, service: AdminService, actor: str) -> None:
    runs = service.runs(limit=100)
    status = service.bot_status()
    feedback_summary = dict(service.feedback_summary())
    total_feedback = sum(feedback_summary.values())
    latest = runs[0] if runs else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bot", status.get("state", "unknown").capitalize())
    c2.metric("Total runs", str(len(runs)))
    c3.metric("Sources", str(sum(len(v) for v in service.list_sources().values())))
    c4.metric("Feedback", str(total_feedback))

    st.markdown("### Action center")
    with st.container(horizontal=True, horizontal_alignment="left"):
        if st.button("Run digest now", type="primary"):
            ok, msg = service.run_now(actor)
            st.success(f"Run started: {msg}") if ok else st.warning(msg)
        if st.button("Restart bot"):
            ok, msg = service.bot_restart(actor)
            st.success(msg) if ok else st.warning(msg)
    st.caption("Use Sources to add/remove feeds, repos, orgs, and queries.")

    st.markdown("### Latest run")
    if latest is None:
        st.info("No runs yet.")
        return

    s1, s2, s3 = st.columns([2, 1, 4], vertical_alignment="center")
    s1.markdown(f"Run `{latest.run_id}`")
    if hasattr(st, "badge"):
        color = {"success": "green", "partial": "orange", "failed": "red"}.get(latest.status, "gray")
        with s2:
            st.badge(latest.status, color=color)
    else:
        s2.caption(f"Status: {latest.status}")
    s3.caption(f"Started: {latest.started_at}  |  Window: {latest.window_start} -> {latest.window_end}")


def _render_runs(st, service: AdminService, actor: str) -> None:
    st.subheader("Runs")
    if st.button("Run now", type="primary"):
        ok, msg = service.run_now(actor)
        if ok:
            st.success(f"Run started: {msg}")
        else:
            st.warning(msg)
    runs = service.runs(limit=200)
    statuses = sorted({r.status for r in runs})
    selected = st.multiselect("Filter status", statuses, default=statuses)
    rows = [
        {
            "run_id": r.run_id,
            "status": r.status,
            "started_at": r.started_at,
            "window_start": r.window_start,
            "window_end": r.window_end,
        }
        for r in runs
        if r.status in selected
    ]
    st.dataframe(rows, width="stretch", hide_index=True)


def _render_sources(st, service: AdminService, actor: str, source_types: list[str]) -> None:
    st.subheader("Sources")
    rows = service.list_sources()
    add_tab, remove_tab, browse_tab = st.tabs(["Add source", "Remove source", "Browse"])

    with add_tab:
        with st.form("add_source"):
            source_type = st.selectbox(
                "Source type",
                source_types,
                format_func=lambda s: f"{_SOURCE_META.get(s, {}).get('label', s)} ({s})",
            )
            meta = _SOURCE_META.get(source_type, {})
            st.caption(meta.get("hint", ""))
            value = st.text_input("Source value", placeholder=meta.get("placeholder", ""))
            preview = ""
            preview_error = ""
            if value.strip():
                try:
                    preview = canonicalize_source_value(source_type, value)
                except ValueError as exc:
                    preview_error = str(exc)
            if preview:
                st.caption(f"Canonical value preview: `{preview}`")
            if preview_error:
                st.warning(preview_error)
            if st.form_submit_button("Add source", type="primary"):
                try:
                    ok, canonical = service.add_source(actor, source_type, value)
                    if ok:
                        st.success(f"Added: {canonical}")
                    else:
                        st.info(f"Already present: {canonical}")
                except Exception as exc:
                    st.error(str(exc))

    with remove_tab:
        source_type_r = st.selectbox(
            "Source type to remove",
            source_types,
            key="source_type_remove",
            format_func=lambda s: f"{_SOURCE_META.get(s, {}).get('label', s)} ({s})",
        )
        values = rows.get(source_type_r, [])
        if not values:
            st.info("No sources for this type.")
        else:
            value_r = st.selectbox("Select source", values, key="remove_value_select")
            if st.button("Remove selected source"):
                try:
                    ok, canonical = service.remove_source(actor, source_type_r, value_r)
                    if ok:
                        st.success(f"Removed: {canonical}")
                        st.rerun()
                    else:
                        st.info(f"Not found: {canonical}")
                except Exception as exc:
                    st.error(str(exc))

    with browse_tab:
        for stype in source_types:
            vals = rows.get(stype, [])
            with st.expander(f"{stype} ({len(vals)})", expanded=len(vals) > 0):
                st.dataframe([{"value": v} for v in vals], width="stretch", hide_index=True)


def _render_bot(st, service: AdminService, actor: str, cfg) -> None:
    st.subheader("Bot lifecycle")
    status = service.bot_status()
    c1, c2, c3 = st.columns(3)
    c1.metric("State", status.get("state", "unknown"))
    c2.metric("PID", status.get("pid", ""))
    c3.metric("Started at", status.get("started_at", ""))

    log_path = Path(cfg.bot_log_path)
    if log_path.exists():
        st.caption(f"Bot log: `{log_path}`")

    with st.container(horizontal=True, horizontal_alignment="left"):
        if st.button("Start"):
            ok, msg = service.bot_start(actor)
            st.success(msg) if ok else st.warning(msg)
        if st.button("Stop"):
            ok, msg = service.bot_stop(actor)
            st.success(msg) if ok else st.warning(msg)
        if st.button("Restart"):
            ok, msg = service.bot_restart(actor)
            st.success(msg) if ok else st.warning(msg)


def _render_logs(st, service: AdminService) -> None:
    st.subheader("Logs")
    st.caption("Filters are applied only when you click Apply filters.")
    with st.form("logs_filter_form", border=False):
        c1, c2, c3, c4 = st.columns(4)
        run_id = c1.text_input("Run ID", key="logs_run_id")
        stage = c2.text_input("Stage", key="logs_stage")
        level = c3.selectbox("Level", ["", "INFO", "WARNING", "ERROR"], index=0, key="logs_level")
        limit = int(c4.number_input("Limit", min_value=50, max_value=1000, value=300, step=50, key="logs_limit"))
        submitted = st.form_submit_button("Apply filters", type="primary")
    _ = submitted

    rows = service.logs(run_id=run_id, stage=stage, level=level, limit=limit)
    if not rows:
        st.info("No logs found for current filters.")
    else:
        st.dataframe(rows, width="stretch", hide_index=True)
        with st.expander("Raw JSON lines", expanded=False):
            for row in rows[:80]:
                st.code(json.dumps(row, ensure_ascii=True))


def _render_outputs(st, service: AdminService) -> None:
    st.subheader("Outputs")
    out = service.outputs()
    st.markdown(f"**Obsidian latest:** `{out['obsidian_latest'] or 'not found'}`")
    t1, t2 = st.tabs(["Telegram", "Obsidian"])
    with t1:
        raw = out["telegram_preview"]
        st.caption(f"{len(raw)} characters")
        st.code(raw or "No preview available.", language="markdown")
    with t2:
        raw = out["obsidian_preview"]
        st.caption(f"{len(raw)} characters")
        st.code(raw or "No preview available.", language="markdown")


def _render_feedback(st, service: AdminService, actor: str) -> None:
    st.subheader("Feedback")
    with st.form("feedback_form"):
        run_id = st.text_input("run_id")
        item_id = st.text_input("item_id")
        rating = st.number_input("rating", min_value=1, max_value=5, value=3)
        label = st.text_input("label")
        comment = st.text_input("comment")
        if st.form_submit_button("Save"):
            service.add_feedback(actor, run_id=run_id, item_id=item_id, rating=int(rating), label=label, comment=comment)
            st.success("Feedback saved")

    st.markdown("### Rating summary")
    summary = service.feedback_summary()
    st.dataframe([{"rating": r, "count": c} for r, c in summary], width="stretch", hide_index=True)

    st.markdown("### Feedback entries")
    rows = service.feedback(limit=300)
    st.dataframe(
        [
            {
                "id": r[0],
                "run_id": r[1],
                "item_id": r[2],
                "rating": r[3],
                "label": r[4],
                "comment": r[5],
                "created_at": r[6],
            }
            for r in rows
        ],
        width="stretch",
        hide_index=True,
    )

    st.markdown("### Admin audit")
    audits = service.audit(limit=200)
    st.dataframe(
        [
            {
                "id": a[0],
                "actor": a[1],
                "action": a[2],
                "target": a[3],
                "details": a[4],
                "created_at": a[5],
            }
            for a in audits
        ],
        width="stretch",
        hide_index=True,
    )


def _select_page(st) -> str:
    pages = ["Overview", "Runs", "Sources", "Bot", "Logs", "Outputs", "Feedback"]
    st.session_state.setdefault("admin_page", "Overview")
    current = st.session_state.get("admin_page", "Overview")
    if current not in pages:
        current = "Overview"

    with st.sidebar:
        st.subheader("Pages")
        if hasattr(st, "segmented_control"):
            page = st.segmented_control("Navigate", pages, default=current, key="admin_page_nav")
            if page:
                st.session_state["admin_page"] = page
        else:
            st.session_state["admin_page"] = st.selectbox(
                "Page",
                pages,
                index=pages.index(current),
                key="admin_page_nav_select",
            )
    return st.session_state["admin_page"]


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("streamlit is required. Install with: pip install streamlit") from exc

    cfg = load_streamlit_admin_config()
    st.set_page_config(page_title="Digest Admin", layout="wide")
    _inject_css(st)
    st.markdown("<span class='ui-kicker'>Operations</span>", unsafe_allow_html=True)
    st.markdown("<h1 class='ui-title'>AI Digest Admin</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='ui-sub'>Manage sources, trigger runs, and inspect output quality in one place.</p>",
        unsafe_allow_html=True,
    )

    st.session_state.setdefault("authed", False)

    with st.sidebar:
        st.header("Auth")
        if not st.session_state.authed:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if username == cfg.admin_user and password == cfg.admin_password and cfg.admin_user:
                    st.session_state.authed = True
                    st.session_state.actor = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        else:
            st.success(f"Logged in as {st.session_state.get('actor', 'admin')}")
            if st.button("Logout"):
                st.session_state.authed = False
                st.session_state.actor = ""
                st.rerun()

    if not st.session_state.authed:
        st.info("Login required")
        return

    service = _get_service(st, cfg)
    source_types = supported_source_types()
    page = _select_page(st)
    actor = st.session_state.get("actor", "admin")

    if page == "Overview":
        _render_overview(st, service, actor)
    elif page == "Runs":
        _render_runs(st, service, actor)
    elif page == "Sources":
        _render_sources(st, service, actor, source_types)
    elif page == "Bot":
        _render_bot(st, service, actor, cfg)
    elif page == "Logs":
        _render_logs(st, service)
    elif page == "Outputs":
        _render_outputs(st, service)
    elif page == "Feedback":
        _render_feedback(st, service, actor)


if __name__ == "__main__":
    main()
