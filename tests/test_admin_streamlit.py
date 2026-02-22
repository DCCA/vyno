import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from digest.admin_streamlit.config import load_streamlit_admin_config
from digest.cli import _cmd_admin_streamlit


class TestAdminStreamlit(unittest.TestCase):
    def test_load_streamlit_admin_config_from_env(self):
        with patch.dict(
            "os.environ",
            {
                "ADMIN_STREAMLIT_SOURCES": "a.yaml",
                "ADMIN_STREAMLIT_PROFILE": "b.yaml",
                "ADMIN_STREAMLIT_DB": "c.db",
                "ADMIN_STREAMLIT_OVERLAY": "d.yaml",
                "ADMIN_STREAMLIT_RUN_LOCK": "e.lock",
                "ADMIN_STREAMLIT_BOT_PID": "f.pid",
                "ADMIN_STREAMLIT_BOT_LOG": "g.log",
                "ADMIN_PANEL_USER": "u",
                "ADMIN_PANEL_PASSWORD": "p",
            },
            clear=False,
        ):
            cfg = load_streamlit_admin_config()
        self.assertEqual(cfg.sources_path, "a.yaml")
        self.assertEqual(cfg.profile_path, "b.yaml")
        self.assertEqual(cfg.db_path, "c.db")
        self.assertEqual(cfg.overlay_path, "d.yaml")
        self.assertEqual(cfg.run_lock_path, "e.lock")
        self.assertEqual(cfg.bot_pid_path, "f.pid")
        self.assertEqual(cfg.bot_log_path, "g.log")
        self.assertEqual(cfg.admin_user, "u")

    def test_cmd_admin_streamlit_invokes_streamlit(self):
        args = argparse.Namespace(
            sources="config/sources.yaml",
            profile="config/profile.yaml",
            db="digest.db",
            sources_overlay="data/sources.local.yaml",
            run_lock_path=".runtime/run.lock",
            bot_pid_path=".runtime/bot.pid",
            bot_log_path=".runtime/bot.out",
            host="127.0.0.1",
            port=8788,
        )
        with patch("subprocess.run") as run_mock:
            _cmd_admin_streamlit(args)
        called = run_mock.call_args
        self.assertIsNotNone(called)
        cmd = called.args[0]
        self.assertEqual(cmd[0], "streamlit")
        self.assertIn("src/digest/admin_streamlit/app.py", cmd)
        env = called.kwargs.get("env")
        self.assertEqual(env["ADMIN_STREAMLIT_SOURCES"], "config/sources.yaml")


if __name__ == "__main__":
    unittest.main()
