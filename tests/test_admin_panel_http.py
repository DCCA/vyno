import http.client
import re
import tempfile
import threading
import time
import unittest
import urllib.parse
from pathlib import Path

from digest.admin.app import create_admin_server
from digest.admin.service import AdminConfig, AdminService


class TestAdminPanelHTTP(unittest.TestCase):
    def _start_server(self):
        tmp = tempfile.TemporaryDirectory()
        base_sources = Path(tmp.name) / "sources.yaml"
        base_profile = Path(tmp.name) / "profile.yaml"
        base_sources.write_text("rss_feeds: ['https://example.com/rss.xml']\n", encoding="utf-8")
        base_profile.write_text("output:\n  obsidian_vault_path: ''\n", encoding="utf-8")
        cfg = AdminConfig(
            sources_path=str(base_sources),
            profile_path=str(base_profile),
            db_path=str(Path(tmp.name) / "digest.db"),
            overlay_path=str(Path(tmp.name) / "sources.local.yaml"),
            run_lock_path=str(Path(tmp.name) / "run.lock"),
            bot_pid_path=str(Path(tmp.name) / "bot.pid"),
            bot_log_path=str(Path(tmp.name) / "bot.out"),
        )
        svc = AdminService(cfg)
        svc.run_now = lambda actor: (True, "testrun")  # type: ignore[method-assign]
        try:
            server = create_admin_server(host="127.0.0.1", port=0, service=svc, admin_user="admin", admin_password="secret")
        except PermissionError:
            tmp.cleanup()
            self.skipTest("Socket binding not permitted in this environment")
        th = threading.Thread(target=server.serve_forever, daemon=True)
        th.start()
        return tmp, svc, server

    def test_login_csrf_and_smoke_flow(self):
        tmp, svc, server = self._start_server()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        self.addCleanup(tmp.cleanup)

        port = server.server_address[1]
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)

        conn.request("GET", "/admin/runs")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 303)
        self.assertIn("/admin/login", resp.getheader("Location"))
        resp.read()

        body = urllib.parse.urlencode({"username": "admin", "password": "secret"})
        conn.request("POST", "/admin/login", body=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 303)
        cookie = resp.getheader("Set-Cookie")
        self.assertIn("admin_session", cookie)
        resp.read()

        headers = {"Cookie": cookie}
        conn.request("GET", "/admin/sources", headers=headers)
        resp = conn.getresponse()
        page = resp.read().decode("utf-8")
        self.assertEqual(resp.status, 200)
        m = re.search(r"name='csrf' value='([^']+)'", page)
        self.assertIsNotNone(m)
        csrf = m.group(1)

        bad_form = urllib.parse.urlencode({"csrf": "bad", "source_type": "github_org", "value": "vercel-labs"})
        conn.request("POST", "/admin/sources/add", body=bad_form, headers={**headers, "Content-Type": "application/x-www-form-urlencoded"})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 403)
        resp.read()

        good_form = urllib.parse.urlencode({"csrf": csrf, "source_type": "github_org", "value": "https://github.com/vercel-labs"})
        conn.request("POST", "/admin/sources/add", body=good_form, headers={**headers, "Content-Type": "application/x-www-form-urlencoded"})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 303)
        resp.read()

        conn.request("GET", "/admin/sources", headers=headers)
        resp = conn.getresponse()
        page2 = resp.read().decode("utf-8")
        self.assertIn("vercel-labs", page2)

        # run trigger smoke (no active lock expected)
        m2 = re.search(r"name='csrf' value='([^']+)'", page2)
        csrf2 = m2.group(1)
        form_run = urllib.parse.urlencode({"csrf": csrf2})
        conn.request("POST", "/admin/runs/trigger", body=form_run, headers={**headers, "Content-Type": "application/x-www-form-urlencoded"})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 303)
        resp.read()

        # feedback add
        conn.request("GET", "/admin/feedback", headers=headers)
        resp = conn.getresponse()
        fb_page = resp.read().decode("utf-8")
        m3 = re.search(r"name='csrf' value='([^']+)'", fb_page)
        csrf3 = m3.group(1)
        form_fb = urllib.parse.urlencode(
            {"csrf": csrf3, "run_id": "r1", "item_id": "i1", "rating": "4", "label": "ok", "comment": "fine"}
        )
        conn.request("POST", "/admin/feedback/add", body=form_fb, headers={**headers, "Content-Type": "application/x-www-form-urlencoded"})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 303)
        resp.read()

        # allow async run thread settle quickly
        time.sleep(0.05)
        conn.close()


if __name__ == "__main__":
    unittest.main()
