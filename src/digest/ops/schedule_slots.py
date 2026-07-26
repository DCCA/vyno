"""Profile-driven schedule slot logic for the CLI scheduler loop.

Pure functions ported from the retired web control plane's scheduler so the
`digest schedule` loop honors ``profile.schedule`` (which the Telegram bot
edits): cadence, local time, quiet hours, timezone, exactly-once per slot
with same-day catch-up.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo


def schedule_config_from_profile(profile_cfg: Any) -> dict[str, Any]:
    schedule = getattr(profile_cfg, "schedule", None)
    return {
        "enabled": bool(getattr(schedule, "enabled", False)),
        "cadence": str(getattr(schedule, "cadence", "daily") or "daily"),
        "time_local": str(getattr(schedule, "time_local", "09:00") or "09:00"),
        "hourly_minute": int(getattr(schedule, "hourly_minute", 0) or 0),
        "quiet_hours_enabled": bool(getattr(schedule, "quiet_hours_enabled", False)),
        "quiet_start_local": str(
            getattr(schedule, "quiet_start_local", "22:00") or "22:00"
        ),
        "quiet_end_local": str(getattr(schedule, "quiet_end_local", "07:00") or "07:00"),
        "timezone": str(getattr(schedule, "timezone", "UTC") or "UTC"),
    }


def due_slot_utc(
    *,
    cadence: str = "daily",
    time_local: str = "09:00",
    hourly_minute: int = 0,
    timezone_name: str,
    now_utc: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Most recent slot at or before now, and the following slot (both UTC)."""
    now = now_utc or datetime.now(timezone.utc)
    local_tz = ZoneInfo(timezone_name)
    local_now = now.astimezone(local_tz)
    resolved_cadence = str(cadence or "daily").strip().lower()
    if resolved_cadence == "hourly":
        minute = max(0, min(59, int(hourly_minute)))
        due_local = local_now.replace(minute=minute, second=0, microsecond=0)
        if local_now < due_local:
            due_local = due_local - timedelta(hours=1)
        next_local = due_local + timedelta(hours=1)
    else:
        hour, minute = [int(part) for part in time_local.split(":", 1)]
        due_local = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if local_now < due_local:
            due_local = due_local - timedelta(days=1)
        next_local = due_local + timedelta(days=1)
    return due_local.astimezone(timezone.utc), next_local.astimezone(timezone.utc)


def _local_hhmm_minutes(value: str) -> int:
    hour, minute = [int(part) for part in str(value or "00:00").split(":", 1)]
    return hour * 60 + minute


def is_quiet_hours_active(schedule: dict[str, Any], *, local_dt: datetime) -> bool:
    if not bool(schedule.get("quiet_hours_enabled", False)):
        return False
    start_minutes = _local_hhmm_minutes(str(schedule.get("quiet_start_local", "22:00")))
    end_minutes = _local_hhmm_minutes(str(schedule.get("quiet_end_local", "07:00")))
    current_minutes = local_dt.hour * 60 + local_dt.minute
    if start_minutes == end_minutes:
        return False
    if start_minutes < end_minutes:
        return start_minutes <= current_minutes < end_minutes
    return current_minutes >= start_minutes or current_minutes < end_minutes


def evaluate_schedule_tick(
    profile_cfg: Any, now_utc: datetime, last_triggered_slot: str
) -> tuple[str, str]:
    """Decide what the scheduler loop should do right now.

    Returns (action, slot_iso) with action one of:
    "disabled", "quiet", "wait", "run". slot_iso identifies the due slot and
    is the exactly-once marker to persist when a run is triggered.
    """
    schedule = schedule_config_from_profile(profile_cfg)
    if not schedule["enabled"]:
        return "disabled", ""
    local_now = now_utc.astimezone(ZoneInfo(schedule["timezone"]))
    if is_quiet_hours_active(schedule, local_dt=local_now):
        return "quiet", ""
    due_slot, _next_slot = due_slot_utc(
        cadence=schedule["cadence"],
        time_local=schedule["time_local"],
        hourly_minute=schedule["hourly_minute"],
        timezone_name=schedule["timezone"],
        now_utc=now_utc,
    )
    due_iso = due_slot.isoformat()
    if now_utc >= due_slot and last_triggered_slot != due_iso:
        return "run", due_iso
    return "wait", due_iso
