import unittest
from datetime import datetime, timezone

from digest.config import ProfileConfig, ScheduleSettings
from digest.ops.schedule_slots import evaluate_schedule_tick


def _profile(**kwargs) -> ProfileConfig:
    defaults = dict(
        enabled=True,
        cadence="daily",
        time_local="07:00",
        timezone="America/Sao_Paulo",
    )
    defaults.update(kwargs)
    return ProfileConfig(schedule=ScheduleSettings(**defaults))


def _utc(y, mo, d, h, mi) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=timezone.utc)


class TestEvaluateScheduleTick(unittest.TestCase):
    # 07:00 America/Sao_Paulo == 10:00 UTC (no DST in 2026)

    def test_disabled_schedule_never_runs(self):
        action, slot = evaluate_schedule_tick(
            _profile(enabled=False), _utc(2026, 7, 26, 10, 0), ""
        )
        self.assertEqual(action, "disabled")

    def test_before_daily_slot_waits(self):
        action, slot = evaluate_schedule_tick(
            _profile(), _utc(2026, 7, 26, 9, 59), "2026-07-25T10:00:00+00:00"
        )
        self.assertEqual(action, "wait")

    def test_at_daily_slot_runs_once(self):
        now = _utc(2026, 7, 26, 10, 0)
        action, slot = evaluate_schedule_tick(_profile(), now, "")
        self.assertEqual(action, "run")
        self.assertEqual(slot, "2026-07-26T10:00:00+00:00")

        action2, _ = evaluate_schedule_tick(_profile(), now, slot)
        self.assertEqual(action2, "wait")

    def test_restart_after_slot_minute_catches_up(self):
        # Process was down at 07:00 local; restarted hours later the same day.
        action, slot = evaluate_schedule_tick(
            _profile(), _utc(2026, 7, 26, 14, 30), "2026-07-25T10:00:00+00:00"
        )
        self.assertEqual(action, "run")
        self.assertEqual(slot, "2026-07-26T10:00:00+00:00")

    def test_hourly_cadence_uses_minute(self):
        profile = _profile(cadence="hourly", hourly_minute=15)
        action, slot = evaluate_schedule_tick(profile, _utc(2026, 7, 26, 12, 20), "")
        self.assertEqual(action, "run")
        self.assertEqual(slot, "2026-07-26T12:15:00+00:00")

        action2, _ = evaluate_schedule_tick(profile, _utc(2026, 7, 26, 12, 20), slot)
        self.assertEqual(action2, "wait")

    def test_quiet_hours_holds_the_trigger(self):
        profile = _profile(
            quiet_hours_enabled=True,
            quiet_start_local="06:00",
            quiet_end_local="08:00",
        )
        # 07:05 local is inside quiet hours
        action, slot = evaluate_schedule_tick(profile, _utc(2026, 7, 26, 10, 5), "")
        self.assertEqual(action, "quiet")

    def test_overnight_quiet_window_wraps_midnight(self):
        profile = _profile(
            time_local="23:00",
            quiet_hours_enabled=True,
            quiet_start_local="22:00",
            quiet_end_local="07:00",
        )
        # 23:30 local (02:30 UTC next day) is inside the wrapped window
        action, _ = evaluate_schedule_tick(profile, _utc(2026, 7, 27, 2, 30), "")
        self.assertEqual(action, "quiet")


if __name__ == "__main__":
    unittest.main()
