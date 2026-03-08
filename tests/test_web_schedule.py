import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from digest.web.app import (
    WebSettings,
    _next_allowed_schedule_slot_utc,
    _schedule_due_slot_utc,
    create_app,
)


class TestWebSchedule(unittest.TestCase):
    def _routes(self, tmp: str):
        root = Path(__file__).resolve().parents[1]
        settings = WebSettings(
            sources_path=str(root / "config" / "sources.yaml"),
            sources_overlay_path=str(Path(tmp) / "sources.local.yaml"),
            profile_path=str(root / "config" / "profile.yaml"),
            profile_overlay_path=str(Path(tmp) / "profile.local.yaml"),
            db_path=str(Path(tmp) / "digest.db"),
            run_lock_path=str(Path(tmp) / "run.lock"),
            history_dir=str(Path(tmp) / "history"),
            onboarding_state_path=str(Path(tmp) / "onboarding-state.json"),
            schedule_state_path=str(Path(tmp) / "schedule-state.json"),
        )
        app = create_app(settings)
        return [route for route in app.routes if getattr(route, "path", None)]

    def _route(self, routes, path: str, method: str):
        for route in routes:
            methods = set(getattr(route, "methods", set()) or set())
            if str(getattr(route, "path")) == path and method.upper() in methods:
                return route.endpoint
        raise KeyError(f"{method} {path}")

    def test_schedule_due_slot_computes_current_and_next_window(self):
        due_slot, next_slot = _schedule_due_slot_utc(
            time_local="09:00",
            timezone_name="UTC",
            now_utc=datetime(2026, 3, 7, 10, 15, tzinfo=timezone.utc),
        )
        self.assertEqual(due_slot.isoformat(), "2026-03-07T09:00:00+00:00")
        self.assertEqual(next_slot.isoformat(), "2026-03-08T09:00:00+00:00")

    def test_hourly_schedule_due_slot_uses_top_of_hour(self):
        due_slot, next_slot = _schedule_due_slot_utc(
            cadence="hourly",
            hourly_minute=0,
            timezone_name="America/Sao_Paulo",
            now_utc=datetime(2026, 3, 7, 13, 15, tzinfo=timezone.utc),
        )
        self.assertEqual(due_slot.isoformat(), "2026-03-07T13:00:00+00:00")
        self.assertEqual(next_slot.isoformat(), "2026-03-07T14:00:00+00:00")

    def test_quiet_hours_push_next_allowed_run_to_morning(self):
        next_slot = _next_allowed_schedule_slot_utc(
            schedule={
                "enabled": True,
                "cadence": "hourly",
                "time_local": "09:00",
                "hourly_minute": 0,
                "quiet_hours_enabled": True,
                "quiet_start_local": "22:00",
                "quiet_end_local": "07:00",
                "timezone": "America/Sao_Paulo",
            },
            now_utc=datetime(2026, 3, 8, 1, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(next_slot.isoformat(), "2026-03-08T10:00:00+00:00")

    def test_schedule_endpoints_save_and_report_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            routes = self._routes(tmp)
            post_schedule = self._route(routes, "/api/config/schedule", "POST")
            get_schedule = self._route(routes, "/api/config/schedule", "GET")
            get_status = self._route(routes, "/api/schedule/status", "GET")

            saved = post_schedule(
                {
                    "enabled": True,
                    "cadence": "hourly",
                    "time_local": "08:45",
                    "hourly_minute": 0,
                    "quiet_hours_enabled": True,
                    "quiet_start_local": "22:00",
                    "quiet_end_local": "07:00",
                    "timezone": "America/Sao_Paulo",
                }
            )
            self.assertTrue(saved["saved"])
            self.assertTrue(saved["schedule"]["enabled"])
            self.assertEqual(saved["schedule"]["cadence"], "hourly")
            self.assertEqual(saved["schedule"]["hourly_minute"], 0)

            loaded = get_schedule()
            self.assertTrue(loaded["schedule"]["enabled"])
            self.assertEqual(loaded["schedule"]["timezone"], "America/Sao_Paulo")

            status = get_status()
            payload = status["schedule_status"]
            self.assertTrue(payload["enabled"])
            self.assertEqual(payload["cadence"], "hourly")
            self.assertTrue(payload["next_run_at"])


if __name__ == "__main__":
    unittest.main()
