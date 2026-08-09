import argparse
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from digest import cli
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


class _StopLoop(Exception):
    """Breaks the scheduler's infinite loop after one tick."""


class TestScheduleStateFile(unittest.TestCase):
    def test_trigger_writes_only_the_keys_the_scheduler_owns(self):
        # Keys left behind by the retired web console. The scheduler used to
        # copy them forward on every trigger, so the file kept advertising a
        # July next_run_at and a frozen copy of profile.schedule.
        stale = {
            "enabled": True,
            "cadence": "daily",
            "timezone": "America/Sao_Paulo",
            "scheduler_status": "running",
            "next_run_at": "2026-07-27T12:00:00+00:00",
            "last_error": "",
            "quiet_hours_active": False,
            "last_triggered_slot": "2026-08-08T12:00:00+00:00",
            "last_triggered_at": "2026-08-08T12:00:05+00:00",
        }
        slot = "2026-08-09T12:00:00+00:00"

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "schedule-state.json"
            state_path.write_text(json.dumps(stale), encoding="utf-8")
            args = argparse.Namespace(
                profile="config/profile.yaml",
                profile_overlay="data/profile.local.yaml",
                sources="config/sources.yaml",
                sources_overlay="data/sources.local.yaml",
                db=str(Path(tmp) / "digest.db"),
            )

            with (
                patch.object(cli, "SCHEDULE_STATE_PATH", str(state_path)),
                patch.object(cli, "load_effective_profile", return_value=_profile()),
                patch.object(
                    cli, "evaluate_schedule_tick", return_value=("run", slot)
                ),
                patch.object(cli, "_execute_run", return_value=0),
                patch.object(cli.time, "sleep", side_effect=_StopLoop),
            ):
                with self.assertRaises(_StopLoop):
                    cli._cmd_schedule(args)

            written = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(
            set(written), {"last_triggered_slot", "last_triggered_at"}
        )
        self.assertEqual(written["last_triggered_slot"], slot)


if __name__ == "__main__":
    unittest.main()
