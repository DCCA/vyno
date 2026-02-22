import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from digest.admin.service import AdminConfig, AdminService


class TestAdminService(unittest.TestCase):
    def _svc(self, tmp: str) -> AdminService:
        base_sources = Path(tmp) / "sources.yaml"
        base_profile = Path(tmp) / "profile.yaml"
        base_sources.write_text("rss_feeds: ['https://example.com/rss.xml']\n", encoding="utf-8")
        base_profile.write_text("output:\n  obsidian_vault_path: ''\n", encoding="utf-8")
        cfg = AdminConfig(
            sources_path=str(base_sources),
            profile_path=str(base_profile),
            db_path=str(Path(tmp) / "digest.db"),
            overlay_path=str(Path(tmp) / "sources.local.yaml"),
            run_lock_path=str(Path(tmp) / "run.lock"),
            bot_pid_path=str(Path(tmp) / "bot.pid"),
            bot_log_path=str(Path(tmp) / "bot.out"),
        )
        return AdminService(cfg)

    def test_source_add_remove_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            svc = self._svc(tmp)
            created, v = svc.add_source("admin", "github_org", "https://github.com/vercel-labs")
            self.assertTrue(created)
            self.assertEqual(v, "vercel-labs")

            rows = svc.list_sources()
            self.assertIn("vercel-labs", rows["github_org"])

            removed, v2 = svc.remove_source("admin", "github_org", "vercel-labs")
            self.assertTrue(removed)
            self.assertEqual(v2, "vercel-labs")
            self.assertTrue(svc.audit(limit=10))

    def test_run_now_respects_active_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            svc = self._svc(tmp)
            Path(svc.cfg.run_lock_path).write_text(json.dumps({"run_id": "abc", "started_at": "2099-01-01T00:00:00+00:00"}), encoding="utf-8")
            ok, msg = svc.run_now("admin")
            self.assertFalse(ok)
            self.assertIn("active:", msg)

    def test_logs_filtering(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict("os.environ", {"DIGEST_LOG_PATH": str(Path(tmp) / "digest.log")}, clear=False):
            svc = self._svc(tmp)
            p = Path(tmp) / "digest.log"
            p.write_text(
                "\n".join(
                    [
                        json.dumps({"run_id": "r1", "stage": "fetch", "level": "INFO", "message": "a"}),
                        json.dumps({"run_id": "r2", "stage": "score", "level": "ERROR", "message": "b"}),
                    ]
                ),
                encoding="utf-8",
            )
            rows = svc.logs(run_id="r2", stage="score", level="ERROR", limit=10)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["run_id"], "r2")

    def test_feedback_crud_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            svc = self._svc(tmp)
            svc.add_feedback("admin", run_id="r1", item_id="i1", rating=5, label="good", comment="nice")
            svc.add_feedback("admin", run_id="r1", item_id="i2", rating=3, label="ok", comment="mid")
            rows = svc.feedback(limit=10)
            self.assertEqual(len(rows), 2)
            summary = dict(svc.feedback_summary())
            self.assertEqual(summary[5], 1)
            self.assertEqual(summary[3], 1)

    def test_bot_start_stop_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            svc = self._svc(tmp)
            fake_proc = MagicMock()
            fake_proc.pid = 12345
            with patch("subprocess.Popen", return_value=fake_proc), patch("digest.admin.service._pid_alive", return_value=True):
                ok, pid = svc.bot_start("admin")
                self.assertTrue(ok)
                self.assertEqual(pid, "12345")
                status = svc.bot_status()
                self.assertEqual(status["state"], "running")
            with patch("os.kill"):
                ok2, _ = svc.bot_stop("admin")
                self.assertTrue(ok2)


if __name__ == "__main__":
    unittest.main()
