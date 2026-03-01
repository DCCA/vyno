from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from digest.cli import _cmd_bot_health_check


class TestBotHealthCheck(unittest.TestCase):
    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    def _args(self, health_path: str, stale_seconds: int = 90, max_error_streak: int = 5) -> argparse.Namespace:
        return argparse.Namespace(
            health_path=health_path,
            stale_seconds=stale_seconds,
            max_error_streak=max_error_streak,
        )

    def test_passes_for_recent_ok_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "bot-health.json"
            payload = {
                "status": "ok",
                "updated_at": self._utc_now().isoformat(timespec="seconds").replace("+00:00", "Z"),
                "last_ok_at": self._utc_now().isoformat(timespec="seconds").replace("+00:00", "Z"),
                "consecutive_errors": 0,
                "poll_timeout_s": 30,
                "last_error": "",
            }
            path.write_text(json.dumps(payload), encoding="utf-8")

            code = _cmd_bot_health_check(self._args(str(path)))
            self.assertEqual(code, 0)

    def test_fails_for_stale_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "bot-health.json"
            old_ts = self._utc_now() - timedelta(minutes=5)
            payload = {
                "status": "ok",
                "updated_at": old_ts.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "last_ok_at": old_ts.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "consecutive_errors": 0,
                "poll_timeout_s": 30,
                "last_error": "",
            }
            path.write_text(json.dumps(payload), encoding="utf-8")

            code = _cmd_bot_health_check(self._args(str(path), stale_seconds=60))
            self.assertEqual(code, 1)

    def test_fails_for_error_streak(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "bot-health.json"
            payload = {
                "status": "error",
                "updated_at": self._utc_now().isoformat(timespec="seconds").replace("+00:00", "Z"),
                "last_ok_at": "",
                "consecutive_errors": 9,
                "poll_timeout_s": 30,
                "last_error": "unauthorized",
            }
            path.write_text(json.dumps(payload), encoding="utf-8")

            code = _cmd_bot_health_check(self._args(str(path), max_error_streak=5))
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
