"""Schedule slot, quiet-hours, and status helpers for the web control plane.

These are pure functions extracted from ``digest.web.app``; they operate on
plain dicts and datetimes and hold no route or application state.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo


def _schedule_config_from_profile(profile_cfg: Any) -> dict[str, Any]:
    schedule = getattr(profile_cfg, "schedule", None)
    return {
        "enabled": bool(getattr(schedule, "enabled", False)),
        "cadence": str(getattr(schedule, "cadence", "daily") or "daily"),
        "time_local": str(getattr(schedule, "time_local", "09:00") or "09:00"),
        "hourly_minute": int(getattr(schedule, "hourly_minute", 0) or 0),
        "quiet_hours_enabled": bool(
            getattr(schedule, "quiet_hours_enabled", False)
        ),
        "quiet_start_local": str(
            getattr(schedule, "quiet_start_local", "22:00") or "22:00"
        ),
        "quiet_end_local": str(
            getattr(schedule, "quiet_end_local", "07:00") or "07:00"
        ),
        "timezone": str(getattr(schedule, "timezone", "UTC") or "UTC"),
    }


def _schedule_due_slot_utc(
    *,
    cadence: str = "daily",
    time_local: str = "09:00",
    hourly_minute: int = 0,
    timezone_name: str,
    now_utc: datetime | None = None,
) -> tuple[datetime, datetime]:
    now = now_utc or datetime.now(timezone.utc)
    local_tz = ZoneInfo(timezone_name)
    local_now = now.astimezone(local_tz)
    resolved_cadence = str(cadence or "daily").strip().lower()
    if resolved_cadence == "hourly":
        minute = max(0, min(59, int(hourly_minute)))
        due_local = local_now.replace(
            minute=minute,
            second=0,
            microsecond=0,
        )
        if local_now < due_local:
            due_local = due_local - timedelta(hours=1)
        next_local = due_local + timedelta(hours=1)
    else:
        hour, minute = [int(part) for part in time_local.split(":", 1)]
        due_local = local_now.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )
        if local_now < due_local:
            due_local = due_local - timedelta(days=1)
        next_local = due_local + timedelta(days=1)
    return due_local.astimezone(timezone.utc), next_local.astimezone(timezone.utc)


def _local_hhmm_minutes(value: str) -> int:
    hour, minute = [int(part) for part in str(value or "00:00").split(":", 1)]
    return hour * 60 + minute


def _is_quiet_hours_active(schedule: dict[str, Any], *, local_dt: datetime) -> bool:
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


def _advance_schedule_slot_local(
    local_dt: datetime,
    *,
    cadence: str,
    time_local: str,
) -> datetime:
    if cadence == "hourly":
        return local_dt + timedelta(hours=1)
    hour, minute = [int(part) for part in time_local.split(":", 1)]
    next_local = local_dt + timedelta(days=1)
    return next_local.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _next_allowed_schedule_slot_utc(
    *,
    schedule: dict[str, Any],
    now_utc: datetime | None = None,
) -> datetime:
    now = now_utc or datetime.now(timezone.utc)
    _, next_slot = _schedule_due_slot_utc(
        cadence=str(schedule.get("cadence", "daily")),
        time_local=str(schedule.get("time_local", "09:00")),
        hourly_minute=int(schedule.get("hourly_minute", 0) or 0),
        timezone_name=str(schedule.get("timezone", "UTC")),
        now_utc=now,
    )
    local_tz = ZoneInfo(str(schedule.get("timezone", "UTC")))
    next_local = next_slot.astimezone(local_tz)
    while _is_quiet_hours_active(schedule, local_dt=next_local):
        next_local = _advance_schedule_slot_local(
            next_local,
            cadence=str(schedule.get("cadence", "daily")),
            time_local=str(schedule.get("time_local", "09:00")),
        )
    return next_local.astimezone(timezone.utc)


def _schedule_completion_detail(schedule: dict[str, Any]) -> str:
    timezone_name = str(schedule.get("timezone", "UTC"))
    cadence = str(schedule.get("cadence", "daily"))
    if cadence == "hourly":
        base = f"hourly :{int(schedule.get('hourly_minute', 0) or 0):02d} {timezone_name}"
    else:
        base = f"{schedule.get('time_local', '09:00')} {timezone_name}"
    if bool(schedule.get("quiet_hours_enabled", False)):
        return (
            f"{base} quiet={schedule.get('quiet_start_local', '22:00')}-"
            f"{schedule.get('quiet_end_local', '07:00')}"
        )
    return base


def _schedule_status_payload(
    *,
    profile_cfg: Any,
    state: dict[str, Any],
    active_run_id: str,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    schedule = _schedule_config_from_profile(profile_cfg)
    payload = {
        "enabled": schedule["enabled"],
        "cadence": schedule["cadence"],
        "time_local": schedule["time_local"],
        "hourly_minute": schedule["hourly_minute"],
        "quiet_hours_enabled": schedule["quiet_hours_enabled"],
        "quiet_start_local": schedule["quiet_start_local"],
        "quiet_end_local": schedule["quiet_end_local"],
        "timezone": schedule["timezone"],
        "scheduler_status": "disabled",
        "quiet_hours_active": False,
        "next_run_at": "",
        "last_triggered_at": str(state.get("last_triggered_at", "") or ""),
        "last_attempted_run_id": str(state.get("last_attempted_run_id", "") or ""),
        "last_result": str(state.get("last_result", "") or ""),
        "last_error": str(state.get("last_error", "") or ""),
        "active_run_id": active_run_id,
    }
    if not schedule["enabled"]:
        return payload
    now = now_utc or datetime.now(timezone.utc)
    local_now = now.astimezone(ZoneInfo(schedule["timezone"]))
    payload["quiet_hours_active"] = _is_quiet_hours_active(schedule, local_dt=local_now)
    payload["scheduler_status"] = "running"
    payload["next_run_at"] = _next_allowed_schedule_slot_utc(
        schedule=schedule,
        now_utc=now,
    ).isoformat()
    if active_run_id:
        payload["scheduler_status"] = "run_active"
    elif payload["quiet_hours_active"]:
        payload["scheduler_status"] = "quiet_hours"
    if payload["last_error"]:
        payload["scheduler_status"] = "error"
    return payload
