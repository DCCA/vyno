from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import hmac
import json
import os
from pathlib import Path
import re
import threading
from urllib.parse import urlparse
import uuid
from typing import Any
from zoneinfo import ZoneInfo

from digest.constants import (
    DEFAULT_RUN_ID_LENGTH,
    DEFAULT_RUN_LOCK_STALE_SECONDS,
    WEB_PROGRESS_HISTORY_LIMIT,
)
from digest.config import parse_profile_dict, profile_to_dict
from digest.logging_utils import get_run_logger
from digest.ops.onboarding import (
    OnboardingSettings,
    apply_source_pack,
    apply_source_selection,
    build_onboarding_status,
    list_source_catalog,
    list_source_packs,
    mark_step_completed,
    run_preflight,
)
from digest.ops.profile_registry import (
    load_effective_profile,
    load_effective_profile_dict,
    save_profile_overlay,
)
from digest.ops.run_lock import RunLock
from digest.ops.source_registry import (
    add_source,
    canonicalize_source_value,
    list_sources,
    load_effective_sources,
    remove_source,
    source_key_for,
    supported_source_types,
    visible_source_entries,
)
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore
from digest.web.link_preview import fetch_link_preview_metadata


FETCH_STAGES = {
    "fetch_rss",
    "fetch_youtube_channel",
    "fetch_youtube_query",
    "fetch_x_inbox",
    "fetch_x_selectors",
    "fetch_github",
}

DEFAULT_WEB_CORS_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
]

DEFAULT_WEB_CORS_ORIGIN_REGEX = (
    r"^https?://((localhost|127\.0\.0\.1|0\.0\.0\.0)"
    r"|(10\.\d+\.\d+\.\d+)"
    r"|(192\.168\.\d+\.\d+)"
    r"|(172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+))(:\d+)?$"
)

DEFAULT_WEB_API_AUTH_MODE = "required"
DEFAULT_WEB_API_TOKEN_HEADER = "X-Digest-Api-Token"
ALLOWED_WEB_API_AUTH_MODES = {"required", "optional", "off"}
REDACTED_SECRET = "__REDACTED__"
SECRET_KEY_RE = re.compile(r"(token|secret|password|api[_-]?key)", re.IGNORECASE)


def _cors_allowed_origins() -> list[str]:
    raw = str(os.getenv("DIGEST_WEB_CORS_ORIGINS", "") or "").strip()
    if not raw:
        return list(DEFAULT_WEB_CORS_ORIGINS)

    values = [part.strip() for part in raw.split(",")]
    return [value for value in values if value]


def _cors_allow_origin_regex() -> str:
    raw = str(os.getenv("DIGEST_WEB_CORS_ORIGIN_REGEX", "") or "").strip()
    if raw:
        return raw
    return DEFAULT_WEB_CORS_ORIGIN_REGEX


def _web_api_auth_mode() -> str:
    raw = (
        str(os.getenv("DIGEST_WEB_API_AUTH_MODE", DEFAULT_WEB_API_AUTH_MODE) or "")
        .strip()
        .lower()
    )
    if raw in ALLOWED_WEB_API_AUTH_MODES:
        return raw
    return DEFAULT_WEB_API_AUTH_MODE


def _web_api_token() -> str:
    return str(os.getenv("DIGEST_WEB_API_TOKEN", "") or "").strip()


def _web_api_token_header() -> str:
    raw = str(
        os.getenv("DIGEST_WEB_API_TOKEN_HEADER", DEFAULT_WEB_API_TOKEN_HEADER) or ""
    ).strip()
    if not raw:
        return DEFAULT_WEB_API_TOKEN_HEADER
    return raw


def _api_auth_decision(
    *,
    path: str,
    method: str,
    mode: str,
    configured_token: str,
    presented_token: str,
) -> tuple[bool, int, str]:
    if not path.startswith("/api/"):
        return True, 200, ""
    if method.upper() == "OPTIONS":
        return True, 200, ""
    if path == "/api/health":
        return True, 200, ""
    if mode == "off":
        return True, 200, ""
    if mode == "required" and not configured_token:
        return (
            False,
            503,
            "DIGEST_WEB_API_TOKEN is required when DIGEST_WEB_API_AUTH_MODE=required",
        )
    if configured_token:
        if not presented_token:
            return False, 401, "missing API token"
        if not hmac.compare_digest(presented_token, configured_token):
            return False, 401, "invalid API token"
    return True, 200, ""


def _is_secret_key(key: str) -> bool:
    return bool(SECRET_KEY_RE.search((key or "").strip()))


def _redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _is_secret_key(str(key)):
                if isinstance(item, str):
                    out[key] = REDACTED_SECRET if item else ""
                elif item is None:
                    out[key] = None
                else:
                    out[key] = REDACTED_SECRET
                continue
            out[key] = _redact_secrets(item)
        return out
    if isinstance(value, list):
        return [_redact_secrets(item) for item in value]
    return value


def _rehydrate_redacted_value(candidate: Any, current: Any) -> Any:
    if isinstance(candidate, str) and candidate == REDACTED_SECRET:
        return current
    if isinstance(candidate, dict) and isinstance(current, dict):
        out_dict: dict[str, Any] = {}
        for key, item in candidate.items():
            out_dict[key] = _rehydrate_redacted_value(item, current.get(key))
        return out_dict
    if isinstance(candidate, list) and isinstance(current, list):
        out_list: list[Any] = []
        for idx, item in enumerate(candidate):
            ref = current[idx] if idx < len(current) else None
            out_list.append(_rehydrate_redacted_value(item, ref))
        return out_list
    return candidate


RUN_MODE_OPTIONS: dict[str, dict[str, bool]] = {
    "fresh_only": {
        "use_last_completed_window": True,
        "only_new": True,
        "allow_seen_fallback": False,
    },
    "balanced": {
        "use_last_completed_window": True,
        "only_new": True,
        "allow_seen_fallback": True,
    },
    "replay_recent": {
        "use_last_completed_window": True,
        "only_new": False,
        "allow_seen_fallback": True,
    },
    "backfill": {
        "use_last_completed_window": False,
        "only_new": False,
        "allow_seen_fallback": True,
    },
}
DEFAULT_WEB_RUN_MODE = "fresh_only"


def _resolve_run_mode(mode: str, *, fallback: str = DEFAULT_WEB_RUN_MODE) -> str:
    candidate = (mode or "").strip().lower()
    if candidate in RUN_MODE_OPTIONS:
        return candidate
    return fallback


def _resolve_profile_run_mode(profile_cfg: Any) -> str:
    run_policy = getattr(profile_cfg, "run_policy", None)
    default_mode = getattr(run_policy, "default_mode", "")
    return _resolve_run_mode(str(default_mode or ""), fallback=DEFAULT_WEB_RUN_MODE)


def _resolve_run_mode_for_request(
    *,
    profile_cfg: Any,
    requested_mode: str,
) -> str:
    default_mode = _resolve_profile_run_mode(profile_cfg)
    run_policy = getattr(profile_cfg, "run_policy", None)
    allow_override = bool(getattr(run_policy, "allow_run_override", True))
    if not allow_override:
        return default_mode
    resolved_requested = _resolve_run_mode(requested_mode, fallback="")
    if resolved_requested:
        return resolved_requested
    return default_mode


def _run_mode_options(mode: str) -> dict[str, bool]:
    resolved_mode = _resolve_run_mode(mode, fallback=DEFAULT_WEB_RUN_MODE)
    return dict(RUN_MODE_OPTIONS[resolved_mode])


def _web_live_run_options(*, trigger: str, mode: str = "") -> dict[str, bool]:
    if trigger in {"web", "schedule"}:
        return _run_mode_options(_resolve_run_mode(mode, fallback=DEFAULT_WEB_RUN_MODE))
    return {
        "use_last_completed_window": False,
        "only_new": False,
        "allow_seen_fallback": True,
    }


@dataclass(slots=True)
class WebSettings:
    sources_path: str
    sources_overlay_path: str
    profile_path: str
    profile_overlay_path: str
    db_path: str
    run_lock_path: str
    run_lock_stale_seconds: int = DEFAULT_RUN_LOCK_STALE_SECONDS
    history_dir: str = ".runtime/config-history"
    onboarding_state_path: str = ".runtime/onboarding-state.json"
    schedule_state_path: str = ".runtime/schedule-state.json"


def _read_json_dict(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json_dict(path: str, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    tmp.replace(p)


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


def create_app(settings: WebSettings):
    try:
        from fastapi import Body, FastAPI, HTTPException, Request
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "FastAPI and pydantic are required for web mode. Install optional web deps."
        ) from exc

    app = FastAPI(title="Digest Config Console API", version="0.1.0")
    auth_mode = _web_api_auth_mode()
    auth_token = _web_api_token()
    auth_header = _web_api_token_header()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_allowed_origins(),
        allow_origin_regex=_cors_allow_origin_regex(),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def require_api_token(request: Request, call_next: Any) -> Any:
        allowed, status_code, detail = _api_auth_decision(
            path=request.url.path,
            method=request.method,
            mode=auth_mode,
            configured_token=auth_token,
            presented_token=str(request.headers.get(auth_header, "") or "").strip(),
        )
        if not allowed:
            return JSONResponse(status_code=status_code, content={"detail": detail})
        return await call_next(request)

    lock = RunLock(
        settings.run_lock_path, stale_seconds=settings.run_lock_stale_seconds
    )
    timeline_store = SQLiteStore(settings.db_path)

    onboarding_settings = OnboardingSettings(
        sources_path=settings.sources_path,
        sources_overlay_path=settings.sources_overlay_path,
        profile_path=settings.profile_path,
        profile_overlay_path=settings.profile_overlay_path,
        db_path=settings.db_path,
        run_lock_path=settings.run_lock_path,
        history_dir=settings.history_dir,
        onboarding_state_path=settings.onboarding_state_path,
    )

    progress_lock = threading.Lock()
    run_progress: dict[str, dict[str, Any]] = {}
    run_progress_order: list[str] = []
    latest_progress_run_id: str | None = None
    schedule_state_lock = threading.Lock()
    schedule_stop_event = threading.Event()

    def _load_schedule_state() -> dict[str, Any]:
        with schedule_state_lock:
            return _read_json_dict(settings.schedule_state_path)

    def _save_schedule_state(**updates: Any) -> dict[str, Any]:
        with schedule_state_lock:
            current = _read_json_dict(settings.schedule_state_path)
            current.update(updates)
            _write_json_dict(settings.schedule_state_path, current)
            return dict(current)

    def _remember_progress_run(run_id: str) -> None:
        nonlocal latest_progress_run_id
        if run_id in run_progress_order:
            run_progress_order.remove(run_id)
        run_progress_order.append(run_id)
        latest_progress_run_id = run_id
        while len(run_progress_order) > WEB_PROGRESS_HISTORY_LIMIT:
            stale = run_progress_order.pop(0)
            run_progress.pop(stale, None)

    def _init_run_progress(*, run_id: str, mode: str) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        with progress_lock:
            _remember_progress_run(run_id)
            run_progress[run_id] = {
                "run_id": run_id,
                "pipeline_run_id": "",
                "_timeline_run_id": run_id,
                "mode": mode,
                "stage": "queued",
                "stage_label": _run_stage_label("queued"),
                "message": "Queued digest run",
                "stage_detail": "Starting worker and loading configuration.",
                "elapsed_s": 0.0,
                "percent": 1.0,
                "status": "running",
                "is_active": True,
                "started_at": now_iso,
                "updated_at": now_iso,
                "details": {},
                "event_index": 0,
                "_fetch_total": 0,
                "_fetch_done": 0,
            }
        timeline_store.insert_timeline_event(
            run_id=run_id,
            event_index=0,
            stage="queued",
            severity="info",
            message="Queued digest run",
            elapsed_s=0.0,
            details={"mode": mode},
            ts_utc=now_iso,
        )

    def _set_fetch_plan(run_id: str, sources_cfg: Any) -> None:
        fetch_total = _count_fetch_targets(sources_cfg)
        with progress_lock:
            state = run_progress.get(run_id)
            if state is None:
                return
            state["_fetch_total"] = fetch_total
            details = dict(state.get("details", {}))
            details["fetch_total"] = fetch_total
            state["details"] = details

    def _record_run_progress(run_id: str, event: dict[str, Any]) -> None:
        stage = str(event.get("stage", "")).strip() or "unknown"
        message = str(event.get("message", "")).strip() or "Working"
        elapsed_s = float(event.get("elapsed_s", 0.0) or 0.0)
        pipeline_run_id = str(event.get("run_id", "")).strip()
        raw_details = {
            key: value
            for key, value in event.items()
            if key not in {"run_id", "stage", "message", "elapsed_s"}
        }

        persist_payload: dict[str, Any] | None = None
        timeline_reassign: tuple[str, str] | None = None
        with progress_lock:
            state = run_progress.get(run_id)
            if state is None:
                return
            timeline_run_id = str(state.get("_timeline_run_id", run_id) or run_id)
            if pipeline_run_id and pipeline_run_id != timeline_run_id:
                timeline_reassign = (timeline_run_id, pipeline_run_id)
                timeline_run_id = pipeline_run_id
                state["_timeline_run_id"] = timeline_run_id

            fetch_total = int(state.get("_fetch_total", 0) or 0)
            fetch_done = int(state.get("_fetch_done", 0) or 0)
            if stage in FETCH_STAGES:
                fetch_done += 1
                if fetch_total > 0:
                    fetch_done = min(fetch_done, fetch_total)
                state["_fetch_done"] = fetch_done

            details = dict(raw_details)
            if fetch_total > 0:
                details["fetch_total"] = fetch_total
                details["fetch_done"] = fetch_done

            percent = _estimate_run_progress_percent(
                stage,
                details=details,
                fetch_done=fetch_done,
                fetch_total=fetch_total,
            )
            prior_percent = state.get("percent")
            if isinstance(prior_percent, (int, float)) and isinstance(
                percent, (int, float)
            ):
                percent = max(float(prior_percent), float(percent))

            if stage == "run_finish":
                status = str(details.get("status") or state.get("status") or "success")
                is_active = False
            else:
                status = str(state.get("status") or "running")
                is_active = bool(state.get("is_active", True))

            next_event_index = int(state.get("event_index", 0) or 0) + 1
            updated_at = datetime.now(timezone.utc).isoformat()
            state.update(
                {
                    "pipeline_run_id": pipeline_run_id
                    or str(state.get("pipeline_run_id", "")),
                    "stage": stage,
                    "stage_label": _run_stage_label(stage),
                    "message": message,
                    "stage_detail": _run_stage_detail(stage, details, fallback=message),
                    "elapsed_s": round(elapsed_s, 1),
                    "percent": percent,
                    "status": status,
                    "is_active": is_active,
                    "updated_at": updated_at,
                    "details": details,
                    "event_index": next_event_index,
                }
            )
            persist_payload = {
                "timeline_run_id": timeline_run_id,
                "event_index": next_event_index,
                "ts_utc": updated_at,
                "stage": stage,
                "severity": _timeline_event_severity(stage, details),
                "message": message,
                "elapsed_s": round(elapsed_s, 1),
                "details": details,
            }
        if timeline_reassign is not None:
            timeline_store.reassign_timeline_run_id(
                old_run_id=timeline_reassign[0],
                new_run_id=timeline_reassign[1],
            )
        if persist_payload is not None:
            timeline_store.insert_timeline_event(
                run_id=str(persist_payload["timeline_run_id"]),
                event_index=int(persist_payload["event_index"]),
                ts_utc=str(persist_payload["ts_utc"]),
                stage=str(persist_payload["stage"]),
                severity=str(persist_payload["severity"]),
                message=str(persist_payload["message"]),
                elapsed_s=float(persist_payload["elapsed_s"]),
                details=dict(persist_payload["details"]),
            )

    def _mark_run_progress_terminal(
        run_id: str,
        *,
        status: str,
        stage: str,
        message: str,
        error: str = "",
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        persist_payload: dict[str, Any] | None = None
        with progress_lock:
            state = run_progress.get(run_id)
            if state is None:
                return
            timeline_run_id = str(state.get("_timeline_run_id", run_id) or run_id)
            details = dict(state.get("details", {}))
            if error:
                details["error"] = error
            next_event_index = int(state.get("event_index", 0) or 0) + 1
            state.update(
                {
                    "stage": stage,
                    "stage_label": _run_stage_label(stage),
                    "message": message,
                    "stage_detail": _run_stage_detail(stage, details, fallback=message),
                    "status": status,
                    "is_active": False,
                    "percent": 100.0,
                    "updated_at": now_iso,
                    "details": details,
                    "event_index": next_event_index,
                }
            )
            persist_payload = {
                "timeline_run_id": timeline_run_id,
                "event_index": next_event_index,
                "ts_utc": now_iso,
                "stage": stage,
                "severity": _timeline_event_severity(stage, details),
                "message": message,
                "elapsed_s": float(state.get("elapsed_s") or 0.0),
                "details": details,
            }
        if persist_payload is not None:
            timeline_store.insert_timeline_event(
                run_id=str(persist_payload["timeline_run_id"]),
                event_index=int(persist_payload["event_index"]),
                ts_utc=str(persist_payload["ts_utc"]),
                stage=str(persist_payload["stage"]),
                severity=str(persist_payload["severity"]),
                message=str(persist_payload["message"]),
                elapsed_s=float(persist_payload["elapsed_s"]),
                details=dict(persist_payload["details"]),
            )

    def _resolve_run_progress_snapshot(
        run_id: str | None = None,
    ) -> dict[str, Any] | None:
        with progress_lock:
            target_run_id = run_id
            if not target_run_id:
                active_state = lock.current()
                if active_state is not None:
                    target_run_id = active_state.run_id
            if not target_run_id:
                target_run_id = latest_progress_run_id
            if not target_run_id:
                return None

            state = run_progress.get(target_run_id)
            if state is None:
                return None

            return {
                key: value for key, value in state.items() if not key.startswith("_")
            }

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/config/source-types")
    def source_types() -> dict[str, list[str]]:
        return {"types": supported_source_types()}

    @app.get("/api/config/sources")
    def get_sources() -> dict[str, Any]:
        effective = load_effective_sources(
            settings.sources_path,
            settings.sources_overlay_path,
        )
        rows = list_sources(settings.sources_path, settings.sources_overlay_path)
        rows["x_inbox"] = [effective.x_inbox_path] if effective.x_inbox_path else []
        return {
            "sources": rows,
        }

    @app.post("/api/config/sources/add")
    def post_source_add(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        source_type = str(payload.get("source_type", "") or "").strip()
        value = str(payload.get("value", "") or "").strip()
        if not source_type or not value:
            raise HTTPException(
                status_code=400,
                detail="source_type and value are required",
            )
        created, canonical = add_source(
            settings.sources_path,
            settings.sources_overlay_path,
            source_type,
            value,
        )
        _save_snapshot(
            settings,
            action="source_add",
            details={"source_type": source_type, "value": canonical},
        )
        mark_step_completed(
            settings.onboarding_state_path,
            "sources",
            details=f"{source_type}:{canonical}",
        )
        return {"created": created, "canonical": canonical}

    @app.post("/api/config/sources/remove")
    def post_source_remove(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        source_type = str(payload.get("source_type", "") or "").strip()
        value = str(payload.get("value", "") or "").strip()
        if not source_type or not value:
            raise HTTPException(
                status_code=400,
                detail="source_type and value are required",
            )
        removed, canonical = remove_source(
            settings.sources_path,
            settings.sources_overlay_path,
            source_type,
            value,
        )
        _save_snapshot(
            settings,
            action="source_remove",
            details={"source_type": source_type, "value": canonical},
        )
        mark_step_completed(
            settings.onboarding_state_path,
            "sources",
            details=f"{source_type}:{canonical}",
        )
        return {"removed": removed, "canonical": canonical}

    @app.get("/api/config/profile")
    def get_profile() -> dict[str, Any]:
        effective = load_effective_profile(
            settings.profile_path, settings.profile_overlay_path
        )
        return {"profile": _redact_secrets(profile_to_dict(effective))}

    @app.get("/api/config/run-policy")
    def get_run_policy() -> dict[str, Any]:
        effective = load_effective_profile(
            settings.profile_path, settings.profile_overlay_path
        )
        run_policy = getattr(effective, "run_policy", None)
        default_mode = _resolve_profile_run_mode(effective)
        return {
            "run_policy": {
                "default_mode": default_mode,
                "allow_run_override": bool(
                    getattr(run_policy, "allow_run_override", True)
                ),
                "seen_reset_guard": str(
                    getattr(run_policy, "seen_reset_guard", "confirm")
                ),
            },
            "available_modes": sorted(RUN_MODE_OPTIONS.keys()),
            "recommended_mode": "balanced",
            "effective_default_mode": default_mode,
        }

    @app.post("/api/config/run-policy")
    def post_run_policy(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        effective = load_effective_profile_dict(
            settings.profile_path, settings.profile_overlay_path
        )
        current_policy_raw = effective.get("run_policy", {})
        current_policy = (
            dict(current_policy_raw) if isinstance(current_policy_raw, dict) else {}
        )
        if "default_mode" in payload:
            current_policy["default_mode"] = str(
                payload.get("default_mode", "")
            ).strip()
        if "allow_run_override" in payload:
            current_policy["allow_run_override"] = bool(
                payload.get("allow_run_override")
            )
        if "seen_reset_guard" in payload:
            current_policy["seen_reset_guard"] = str(
                payload.get("seen_reset_guard", "")
            ).strip()
        next_profile = dict(effective)
        next_profile["run_policy"] = current_policy
        save_profile_overlay(
            settings.profile_path,
            settings.profile_overlay_path,
            next_profile,
        )
        _save_snapshot(
            settings,
            action="run_policy_save",
            details={"run_policy": current_policy},
        )
        profile_cfg = load_effective_profile(
            settings.profile_path, settings.profile_overlay_path
        )
        policy = getattr(profile_cfg, "run_policy", None)
        return {
            "saved": True,
            "run_policy": {
                "default_mode": _resolve_profile_run_mode(profile_cfg),
                "allow_run_override": bool(
                    getattr(policy, "allow_run_override", True)
                ),
                "seen_reset_guard": str(
                    getattr(policy, "seen_reset_guard", "confirm")
                ),
            },
        }

    @app.get("/api/config/schedule")
    def get_schedule() -> dict[str, Any]:
        effective = load_effective_profile(
            settings.profile_path,
            settings.profile_overlay_path,
        )
        return {
            "schedule": _schedule_config_from_profile(effective),
        }

    @app.post("/api/config/schedule")
    def post_schedule(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        effective = load_effective_profile_dict(
            settings.profile_path, settings.profile_overlay_path
        )
        current_schedule_raw = effective.get("schedule", {})
        current_schedule = (
            dict(current_schedule_raw) if isinstance(current_schedule_raw, dict) else {}
        )
        if "enabled" in payload:
            current_schedule["enabled"] = bool(payload.get("enabled"))
        if "cadence" in payload:
            current_schedule["cadence"] = str(payload.get("cadence", "") or "").strip()
        if "time_local" in payload:
            current_schedule["time_local"] = str(payload.get("time_local", "") or "").strip()
        if "hourly_minute" in payload:
            current_schedule["hourly_minute"] = payload.get("hourly_minute", 0)
        if "quiet_hours_enabled" in payload:
            current_schedule["quiet_hours_enabled"] = bool(payload.get("quiet_hours_enabled"))
        if "quiet_start_local" in payload:
            current_schedule["quiet_start_local"] = str(payload.get("quiet_start_local", "") or "").strip()
        if "quiet_end_local" in payload:
            current_schedule["quiet_end_local"] = str(payload.get("quiet_end_local", "") or "").strip()
        if "timezone" in payload:
            current_schedule["timezone"] = str(payload.get("timezone", "") or "").strip()
        next_profile = dict(effective)
        next_profile["schedule"] = current_schedule
        save_profile_overlay(
            settings.profile_path,
            settings.profile_overlay_path,
            next_profile,
        )
        _save_snapshot(
            settings,
            action="schedule_save",
            details={"schedule": current_schedule},
        )
        profile_cfg = load_effective_profile(
            settings.profile_path, settings.profile_overlay_path
        )
        schedule_cfg = _schedule_config_from_profile(profile_cfg)
        if schedule_cfg["enabled"]:
            mark_step_completed(
                settings.onboarding_state_path,
                "schedule",
                details=_schedule_completion_detail(schedule_cfg),
            )
        return {"saved": True, "schedule": schedule_cfg}

    @app.get("/api/schedule/status")
    def get_schedule_status() -> dict[str, Any]:
        effective = load_effective_profile(
            settings.profile_path,
            settings.profile_overlay_path,
        )
        _sync_schedule_result_from_store()
        active = lock.current()
        state = _load_schedule_state()
        payload = _schedule_status_payload(
            profile_cfg=effective,
            state=state,
            active_run_id=active.run_id if active is not None else "",
        )
        return {"schedule_status": payload}

    @app.post("/api/config/profile/validate")
    def post_profile_validate(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        profile_data = payload.get("profile")
        if not isinstance(profile_data, dict):
            raise HTTPException(status_code=400, detail="profile object is required")
        current = profile_to_dict(
            load_effective_profile(settings.profile_path, settings.profile_overlay_path)
        )
        hydrated = _rehydrate_redacted_value(profile_data, current)
        validated = parse_profile_dict(hydrated)
        return {"valid": True, "profile": _redact_secrets(profile_to_dict(validated))}

    @app.post("/api/config/profile/diff")
    def post_profile_diff(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        profile_data = payload.get("profile")
        if not isinstance(profile_data, dict):
            raise HTTPException(status_code=400, detail="profile object is required")
        current = profile_to_dict(
            load_effective_profile(settings.profile_path, settings.profile_overlay_path)
        )
        hydrated = _rehydrate_redacted_value(profile_data, current)
        validated = parse_profile_dict(hydrated)
        candidate = profile_to_dict(validated)
        return {
            "diff": _dict_diff(current, candidate),
        }

    @app.post("/api/config/profile/save")
    def post_profile_save(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        profile_data = payload.get("profile")
        if not isinstance(profile_data, dict):
            raise HTTPException(status_code=400, detail="profile object is required")
        current = profile_to_dict(
            load_effective_profile(settings.profile_path, settings.profile_overlay_path)
        )
        hydrated = _rehydrate_redacted_value(profile_data, current)
        overlay = save_profile_overlay(
            settings.profile_path,
            settings.profile_overlay_path,
            hydrated,
        )
        _save_snapshot(
            settings,
            action="profile_save",
            details={"overlay_keys": sorted(overlay.keys())},
        )
        mark_step_completed(
            settings.onboarding_state_path,
            "profile",
            details=f"overlay_keys={','.join(sorted(overlay.keys()))}",
        )
        effective = load_effective_profile(
            settings.profile_path,
            settings.profile_overlay_path,
        )
        if effective.output.telegram_bot_token and effective.output.telegram_chat_id:
            mark_step_completed(
                settings.onboarding_state_path,
                "outputs",
                details="telegram",
            )
        if effective.output.obsidian_vault_path:
            mark_step_completed(
                settings.onboarding_state_path,
                "outputs",
                details="obsidian",
            )
        schedule_cfg = _schedule_config_from_profile(effective)
        if schedule_cfg["enabled"]:
            mark_step_completed(
                settings.onboarding_state_path,
                "schedule",
                details=_schedule_completion_detail(schedule_cfg),
            )
        return {"saved": True, "overlay": _redact_secrets(overlay)}

    @app.get("/api/config/effective")
    def get_effective() -> dict[str, Any]:
        sources_cfg = load_effective_sources(
            settings.sources_path,
            settings.sources_overlay_path,
        )
        profile_cfg = load_effective_profile(
            settings.profile_path,
            settings.profile_overlay_path,
        )
        return {
            "sources": {
                "rss": list(sources_cfg.rss_feeds),
                "youtube_channel": list(sources_cfg.youtube_channels),
                "youtube_query": list(sources_cfg.youtube_queries),
                "x_author": list(sources_cfg.x_authors),
                "x_theme": list(sources_cfg.x_themes),
                "github_repo": list(sources_cfg.github_repos),
                "github_topic": list(sources_cfg.github_topics),
                "github_query": list(sources_cfg.github_search_queries),
                "github_org": list(sources_cfg.github_orgs),
                "x_inbox": [sources_cfg.x_inbox_path]
                if sources_cfg.x_inbox_path
                else [],
            },
            "profile": _redact_secrets(profile_to_dict(profile_cfg)),
        }

    @app.get("/api/config/history")
    def get_history() -> dict[str, Any]:
        path = Path(settings.history_dir)
        if not path.exists():
            return {"snapshots": []}
        snapshots: list[dict[str, Any]] = []
        for file in sorted(path.glob("*.json"), reverse=True):
            try:
                payload = json.loads(file.read_text(encoding="utf-8"))
            except Exception:
                continue
            snapshots.append(
                {
                    "id": file.stem,
                    "created_at": payload.get("created_at", ""),
                    "action": payload.get("action", ""),
                    "details": payload.get("details", {}),
                }
            )
        return {"snapshots": snapshots[:100]}

    @app.post("/api/config/rollback")
    def post_rollback(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        snapshot_id = str(payload.get("snapshot_id", "") or "").strip()
        if not snapshot_id:
            raise HTTPException(status_code=400, detail="snapshot_id is required")
        path = Path(settings.history_dir) / f"{snapshot_id}.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail="snapshot not found")
        data = json.loads(path.read_text(encoding="utf-8"))
        sources_overlay = data.get("sources_overlay", {})
        profile_overlay = data.get("profile_overlay", {})
        current_profile_overlay = _read_yaml_dict(settings.profile_overlay_path)
        profile_overlay = _rehydrate_redacted_value(
            profile_overlay,
            current_profile_overlay,
        )
        _write_yaml_dict(settings.sources_overlay_path, sources_overlay)
        _write_yaml_dict(settings.profile_overlay_path, profile_overlay)
        _save_snapshot(
            settings, action="rollback", details={"snapshot_id": snapshot_id}
        )
        return {"rolled_back": True}

    def _start_live_run(*, mode_override: str = "", trigger: str = "web") -> dict[str, Any]:
        run_request_id = uuid.uuid4().hex[:DEFAULT_RUN_ID_LENGTH]
        acquired, current = lock.acquire(run_request_id)
        if not acquired and current is not None:
            return {
                "started": False,
                "active_run_id": current.run_id,
                "started_at": current.started_at,
            }
        profile = load_effective_profile(
            settings.profile_path,
            settings.profile_overlay_path,
        )
        resolved_mode = _resolve_run_mode_for_request(
            profile_cfg=profile,
            requested_mode=mode_override,
        )
        run_options = _web_live_run_options(trigger=trigger, mode=resolved_mode)

        # Compute effective min_items threshold: only for scheduled runs.
        effective_min_items = 0
        if trigger == "schedule" and profile.min_items_for_delivery > 0:
            effective_min_items = profile.min_items_for_delivery
            # Safety valve: if too long since last real delivery, force it
            store_check = SQLiteStore(settings.db_path)
            last_end = store_check.last_completed_window_end()
            if last_end:
                last_dt = datetime.fromisoformat(last_end)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                hours_since = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
                if hours_since >= profile.max_accumulation_hours:
                    effective_min_items = 0

        _init_run_progress(run_id=run_request_id, mode=resolved_mode)

        def worker() -> None:
            worker_logger = get_run_logger(run_request_id)
            try:
                sources = load_effective_sources(
                    settings.sources_path,
                    settings.sources_overlay_path,
                )
                _set_fetch_plan(run_request_id, sources)
                store = SQLiteStore(settings.db_path)
                run_digest(
                    sources,
                    profile,
                    store,
                    **run_options,
                    min_items_for_delivery=effective_min_items,
                    logger=worker_logger,
                    progress_cb=lambda event: _record_run_progress(
                        run_request_id, event
                    ),
                )
            except Exception as exc:
                _mark_run_progress_terminal(
                    run_request_id,
                    status="failed",
                    stage="run_failed",
                    message="Digest run failed",
                    error=str(exc),
                )
                worker_logger.exception("Digest run worker failed")
            finally:
                lock.release(run_request_id)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return {"started": True, "run_id": run_request_id, "mode": resolved_mode}

    def _sync_schedule_result_from_store() -> None:
        state = _load_schedule_state()
        attempted_run_id = str(state.get("last_attempted_run_id", "") or "")
        if not attempted_run_id:
            return
        store = SQLiteStore(settings.db_path)
        latest = store.latest_run_details(completed_only=True)
        if latest is None or str(latest[0]) != attempted_run_id:
            return
        _save_schedule_state(
            last_result=str(latest[1]),
            last_error="",
        )

    def _scheduler_loop() -> None:
        while not schedule_stop_event.is_set():
            try:
                profile_cfg = load_effective_profile(
                    settings.profile_path,
                    settings.profile_overlay_path,
                )
                schedule_cfg = _schedule_config_from_profile(profile_cfg)
                state = _load_schedule_state()
                active = lock.current()
                active_run_id = active.run_id if active is not None else ""
                now_utc = datetime.now(timezone.utc)
                status_payload = _schedule_status_payload(
                    profile_cfg=profile_cfg,
                    state=state,
                    active_run_id=active_run_id,
                    now_utc=now_utc,
                )
                if not schedule_cfg["enabled"]:
                    _save_schedule_state(
                        enabled=False,
                        cadence=schedule_cfg["cadence"],
                        time_local=schedule_cfg["time_local"],
                        hourly_minute=schedule_cfg["hourly_minute"],
                        quiet_hours_enabled=schedule_cfg["quiet_hours_enabled"],
                        quiet_start_local=schedule_cfg["quiet_start_local"],
                        quiet_end_local=schedule_cfg["quiet_end_local"],
                        timezone=schedule_cfg["timezone"],
                        scheduler_status="disabled",
                        quiet_hours_active=False,
                        next_run_at="",
                        last_error="",
                    )
                    schedule_stop_event.wait(15)
                    continue

                due_slot, _ = _schedule_due_slot_utc(
                    cadence=schedule_cfg["cadence"],
                    time_local=schedule_cfg["time_local"],
                    hourly_minute=schedule_cfg["hourly_minute"],
                    timezone_name=schedule_cfg["timezone"],
                    now_utc=now_utc,
                )
                _sync_schedule_result_from_store()
                next_allowed_slot = _next_allowed_schedule_slot_utc(
                    schedule=schedule_cfg,
                    now_utc=now_utc,
                )
                state = _save_schedule_state(
                    enabled=True,
                    cadence=schedule_cfg["cadence"],
                    time_local=schedule_cfg["time_local"],
                    hourly_minute=schedule_cfg["hourly_minute"],
                    quiet_hours_enabled=schedule_cfg["quiet_hours_enabled"],
                    quiet_start_local=schedule_cfg["quiet_start_local"],
                    quiet_end_local=schedule_cfg["quiet_end_local"],
                    timezone=schedule_cfg["timezone"],
                    scheduler_status=status_payload["scheduler_status"],
                    quiet_hours_active=status_payload["quiet_hours_active"],
                    next_run_at=next_allowed_slot.isoformat(),
                )
                if status_payload["quiet_hours_active"]:
                    schedule_stop_event.wait(15)
                    continue
                last_triggered_slot = str(state.get("last_triggered_slot", "") or "")
                due_slot_iso = due_slot.isoformat()
                if now_utc >= due_slot and last_triggered_slot != due_slot_iso:
                    result = _start_live_run(trigger="schedule")
                    if result.get("started", False):
                        _save_schedule_state(
                            enabled=True,
                            cadence=schedule_cfg["cadence"],
                            time_local=schedule_cfg["time_local"],
                            hourly_minute=schedule_cfg["hourly_minute"],
                            quiet_hours_enabled=schedule_cfg["quiet_hours_enabled"],
                            quiet_start_local=schedule_cfg["quiet_start_local"],
                            quiet_end_local=schedule_cfg["quiet_end_local"],
                            timezone=schedule_cfg["timezone"],
                            scheduler_status="run_active",
                            quiet_hours_active=False,
                            next_run_at=next_allowed_slot.isoformat(),
                            last_triggered_slot=due_slot_iso,
                            last_triggered_at=now_utc.isoformat(),
                            last_attempted_run_id=str(result.get("run_id", "")),
                            last_result="started",
                            last_error="",
                        )
                    else:
                        active_run_id = str(result.get("active_run_id", "") or "")
                        _save_schedule_state(
                            enabled=True,
                            cadence=schedule_cfg["cadence"],
                            time_local=schedule_cfg["time_local"],
                            hourly_minute=schedule_cfg["hourly_minute"],
                            quiet_hours_enabled=schedule_cfg["quiet_hours_enabled"],
                            quiet_start_local=schedule_cfg["quiet_start_local"],
                            quiet_end_local=schedule_cfg["quiet_end_local"],
                            timezone=schedule_cfg["timezone"],
                            scheduler_status="waiting_for_run_lock" if active_run_id else "error",
                            quiet_hours_active=False,
                            next_run_at=next_allowed_slot.isoformat(),
                            last_error=(
                                f"Delayed by active run {active_run_id}"
                                if active_run_id
                                else "Scheduled run could not start"
                            ),
                        )
                elif active_run_id:
                    _save_schedule_state(
                        enabled=True,
                        cadence=schedule_cfg["cadence"],
                        time_local=schedule_cfg["time_local"],
                        hourly_minute=schedule_cfg["hourly_minute"],
                        quiet_hours_enabled=schedule_cfg["quiet_hours_enabled"],
                        quiet_start_local=schedule_cfg["quiet_start_local"],
                        quiet_end_local=schedule_cfg["quiet_end_local"],
                        timezone=schedule_cfg["timezone"],
                        scheduler_status="run_active",
                        quiet_hours_active=False,
                        next_run_at=next_allowed_slot.isoformat(),
                    )
            except Exception as exc:
                _save_schedule_state(
                    scheduler_status="error",
                    last_error=str(exc),
                )
            schedule_stop_event.wait(15)

    @app.on_event("startup")
    def _start_scheduler() -> None:
        schedule_stop_event.clear()
        thread = threading.Thread(target=_scheduler_loop, daemon=True)
        thread.start()
        app.state.schedule_thread = thread

    @app.on_event("shutdown")
    def _stop_scheduler() -> None:
        schedule_stop_event.set()

    @app.post("/api/run-now")
    def post_run_now(payload: dict[str, Any] | None = Body(default=None)) -> dict[str, Any]:
        body = payload if isinstance(payload, dict) else {}
        mode_override = str(body.get("mode", "") or "").strip()
        return _start_live_run(mode_override=mode_override)

    @app.get("/api/onboarding/preflight")
    def get_onboarding_preflight() -> dict[str, Any]:
        report = run_preflight(onboarding_settings)
        if report.get("ok", False):
            mark_step_completed(
                settings.onboarding_state_path,
                "preflight",
                details="preflight_ok",
            )
        return report

    @app.get("/api/onboarding/status")
    def get_onboarding_status() -> dict[str, Any]:
        return build_onboarding_status(onboarding_settings)

    @app.get("/api/onboarding/source-packs")
    def get_onboarding_source_packs() -> dict[str, Any]:
        return {"packs": list_source_packs()}

    @app.post("/api/onboarding/source-packs/apply")
    def post_onboarding_source_pack_apply(
        payload: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        pack_id = str(payload.get("pack_id", "") or "").strip()
        if not pack_id:
            raise HTTPException(status_code=400, detail="pack_id is required")
        try:
            result = apply_source_pack(onboarding_settings, pack_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        _save_snapshot(
            settings,
            action="source_pack_apply",
            details={
                "pack_id": pack_id,
                "added_count": int(result.get("added_count", 0)),
                "error_count": int(result.get("error_count", 0)),
            },
        )

        if (
            int(result.get("added_count", 0)) > 0
            or int(result.get("existing_count", 0)) > 0
        ):
            mark_step_completed(
                settings.onboarding_state_path,
                "sources",
                details=f"pack:{pack_id}",
            )

        return result

    @app.get("/api/onboarding/source-catalog")
    def get_onboarding_source_catalog() -> dict[str, Any]:
        return list_source_catalog(
            settings.sources_path,
            settings.sources_overlay_path,
        )

    @app.post("/api/onboarding/sources/apply-selection")
    def post_onboarding_apply_selection(
        payload: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        entries = payload.get("entries")
        if not isinstance(entries, list):
            raise HTTPException(status_code=400, detail="entries list is required")
        result = apply_source_selection(onboarding_settings, entries)

        _save_snapshot(
            settings,
            action="source_catalog_apply",
            details={
                "added_count": int(result.get("added_count", 0)),
                "error_count": int(result.get("error_count", 0)),
            },
        )

        if (
            int(result.get("added_count", 0)) > 0
            or int(result.get("existing_count", 0)) > 0
        ):
            mark_step_completed(
                settings.onboarding_state_path,
                "sources",
                details="catalog_selection",
            )

        return result

    @app.post("/api/onboarding/preview")
    def post_onboarding_preview() -> dict[str, Any]:
        preview_dir = Path(".runtime/preview")
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_db = preview_dir / f"preview-{uuid.uuid4().hex[:8]}.db"
        report = None

        try:
            sources = load_effective_sources(
                settings.sources_path,
                settings.sources_overlay_path,
            )
            profile = load_effective_profile(
                settings.profile_path,
                settings.profile_overlay_path,
            )
            report = run_digest(
                sources,
                profile,
                SQLiteStore(str(preview_db)),
                use_last_completed_window=False,
                only_new=False,
                preview_mode=True,
                logger=get_run_logger(f"preview-{uuid.uuid4().hex[:8]}"),
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"preview failed: {exc}"
            ) from exc
        finally:
            _cleanup_preview_db(preview_db)

        if report is None:
            raise HTTPException(status_code=500, detail="preview failed: empty report")

        mark_step_completed(
            settings.onboarding_state_path,
            "preview",
            details=report.run_id,
        )

        return {
            "run_id": report.run_id,
            "status": report.status,
            "source_error_count": len(report.source_errors),
            "summary_error_count": len(report.summary_errors),
            "source_errors": list(report.source_errors),
            "summary_errors": list(report.summary_errors),
            "source_count": report.source_count,
            "must_read_count": report.must_read_count,
            "skim_count": report.skim_count,
            "video_count": report.video_count,
            "telegram_messages": list(report.telegram_messages),
            "obsidian_note": report.obsidian_note,
        }

    @app.post("/api/onboarding/activate")
    def post_onboarding_activate() -> dict[str, Any]:
        result = _start_live_run()
        if result.get("started", False):
            mark_step_completed(
                settings.onboarding_state_path,
                "activate",
                details=str(result.get("run_id", "")),
            )
        return result

    @app.get("/api/run-progress")
    def get_run_progress(run_id: str | None = None) -> dict[str, Any]:
        snapshot = _resolve_run_progress_snapshot(run_id=run_id)
        if snapshot is None:
            return {"available": False}
        return {"available": True, **snapshot}

    @app.get("/api/run-status")
    def get_run_status() -> dict[str, Any]:
        store = SQLiteStore(settings.db_path)
        latest = store.latest_run_details(completed_only=False)
        latest_completed = store.latest_run_details(completed_only=True)
        active = lock.current()
        if latest_completed is not None:
            mark_step_completed(
                settings.onboarding_state_path,
                "health",
                details=str(latest_completed[0]),
            )
        return {
            "active": (
                {"run_id": active.run_id, "started_at": active.started_at}
                if active is not None
                else None
            ),
            "latest": (
                {
                    "run_id": latest[0],
                    "status": latest[1],
                    "started_at": latest[2],
                    "source_error_count": len(latest[3]),
                    "summary_error_count": len(latest[4]),
                }
                if latest is not None
                else None
            ),
            "latest_completed": (
                {
                    "run_id": latest_completed[0],
                    "status": latest_completed[1],
                    "started_at": latest_completed[2],
                    "source_error_count": len(latest_completed[3]),
                    "summary_error_count": len(latest_completed[4]),
                    "source_errors": [
                        _parse_source_error(line) for line in latest_completed[3]
                    ],
                }
                if latest_completed is not None
                else None
            ),
        }

    @app.get("/api/timeline/runs")
    def get_timeline_runs(limit: int = 50) -> dict[str, Any]:
        return {"runs": timeline_store.list_timeline_runs(limit=limit)}

    @app.get("/api/timeline/events")
    def get_timeline_events(
        run_id: str,
        limit: int = 200,
        after_event_index: int = -1,
        stage: str = "",
        severity: str = "",
        order: str = "asc",
    ) -> dict[str, Any]:
        rows = timeline_store.list_timeline_events(
            run_id=run_id,
            limit=limit,
            after_event_index=after_event_index,
            stage=stage,
            severity=severity,
            order=order,
        )
        return {"events": rows}

    @app.get("/api/timeline/live")
    def get_timeline_live(
        run_id: str | None = None,
        limit: int = 200,
        after_event_index: int = -1,
        order: str = "asc",
    ) -> dict[str, Any]:
        target_run_id = str(run_id or "").strip()
        if not target_run_id:
            active = lock.current()
            if active is not None:
                target_run_id = active.run_id
        if not target_run_id:
            rows = timeline_store.list_timeline_runs(limit=1)
            if rows:
                target_run_id = str(rows[0].get("run_id", "") or "").strip()
        if not target_run_id:
            return {"run_id": "", "events": []}
        rows = timeline_store.list_timeline_events(
            run_id=target_run_id,
            limit=limit,
            after_event_index=after_event_index,
            order=order,
        )
        return {"run_id": target_run_id, "events": rows}

    @app.get("/api/timeline/summary")
    def get_timeline_summary(run_id: str) -> dict[str, Any]:
        summary = timeline_store.timeline_summary(run_id=run_id)
        if not summary:
            raise HTTPException(status_code=404, detail="run timeline not found")
        return {"summary": summary}

    @app.get("/api/run-items")
    def get_run_items(run_id: str) -> dict[str, Any]:
        return {"items": timeline_store.list_run_items(run_id=run_id)}

    @app.get("/api/run-artifacts")
    def get_run_artifacts(run_id: str) -> dict[str, Any]:
        artifacts = timeline_store.list_run_artifacts(run_id=run_id)
        rows: list[dict[str, Any]] = []
        for row in artifacts:
            path = Path(str(row.get("storage_path") or ""))
            content = ""
            if path.exists():
                try:
                    content = path.read_text(encoding="utf-8")
                except Exception:
                    content = ""
            rows.append({**row, "content": content})
        return {"artifacts": rows}

    @app.get("/api/run-artifacts/list")
    def get_run_artifacts_list(limit: int = 50) -> dict[str, Any]:
        return {"runs": timeline_store.list_archived_runs(limit=limit)}

    @app.get("/api/timeline/notes")
    def get_timeline_notes(run_id: str, limit: int = 100) -> dict[str, Any]:
        return {"notes": timeline_store.list_timeline_notes(run_id=run_id, limit=limit)}

    @app.post("/api/timeline/notes")
    def post_timeline_notes(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        run_id = str(payload.get("run_id", "") or "").strip()
        note = str(payload.get("note", "") or "").strip()
        author = str(payload.get("author", "") or "").strip()
        labels_raw = payload.get("labels", [])
        actions_raw = payload.get("actions", [])
        labels = labels_raw if isinstance(labels_raw, list) else []
        actions = actions_raw if isinstance(actions_raw, list) else []
        if not run_id or not note:
            raise HTTPException(status_code=400, detail="run_id and note are required")
        note_id = timeline_store.add_timeline_note(
            run_id=run_id,
            note=note,
            author=author,
            labels=[str(v) for v in labels],
            actions=[str(v) for v in actions],
        )
        return {"created": bool(note_id), "id": note_id}

    @app.post("/api/feedback/item")
    def post_item_feedback(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        run_id = str(payload.get("run_id", "") or "").strip()
        item_id = str(payload.get("item_id", "") or "").strip()
        label = str(payload.get("label", "") or "").strip().lower()
        comment = str(payload.get("comment", "") or "").strip()
        actor = str(payload.get("actor", "web-admin") or "").strip() or "web-admin"
        if not run_id or not item_id or not label:
            raise HTTPException(status_code=400, detail="run_id, item_id, and label are required")
        item_rows = timeline_store.list_run_items(run_id=run_id)
        item_row = next((row for row in item_rows if str(row.get("item_id") or "") == item_id), None)
        if item_row is None:
            raise HTTPException(status_code=404, detail="run item not found")
        rating = _feedback_rating_for_label(label)
        features = _feedback_features_for_item_feedback(item_row, label=label)
        timeline_store.add_feedback(
            run_id=run_id,
            item_id=item_id,
            rating=rating,
            label=label,
            comment=comment,
            target_kind="item",
            target_key=item_id,
            features=features,
            actor=actor,
        )
        timeline_store.log_admin_action(
            actor=actor,
            action="item_feedback",
            target=item_id,
            details=json.dumps({"run_id": run_id, "label": label}, ensure_ascii=True),
        )
        return {"saved": True, "rating": rating}

    @app.post("/api/feedback/source")
    def post_source_feedback(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        source_type = str(payload.get("source_type", "") or "").strip().lower()
        source_value = str(payload.get("source_value", "") or "").strip()
        label = str(payload.get("label", "") or "").strip().lower()
        comment = str(payload.get("comment", "") or "").strip()
        actor = str(payload.get("actor", "web-admin") or "").strip() or "web-admin"
        if not source_type or not source_value or not label:
            raise HTTPException(status_code=400, detail="source_type, source_value, and label are required")
        rating = _feedback_rating_for_label(label)
        canonical = canonicalize_source_value(source_type, source_value)
        if label == "mute_source":
            updated_profile = _apply_blocked_source_preference(
                settings,
                source_type=source_type,
                source_value=canonical,
            )
            _save_snapshot(
                settings,
                action="source_feedback_mute",
                details={"source_type": source_type, "source_value": canonical},
            )
        else:
            updated_profile = load_effective_profile_dict(
                settings.profile_path,
                settings.profile_overlay_path,
            )
        timeline_store.add_feedback(
            run_id="",
            item_id="",
            rating=rating,
            label=label,
            comment=comment,
            target_kind="source",
            target_key=f"{source_type}:{canonical}",
            features=_feedback_features_for_source_feedback(
                source_type=source_type,
                source_value=canonical,
                label=label,
            ),
            actor=actor,
        )
        timeline_store.log_admin_action(
            actor=actor,
            action="source_feedback",
            target=f"{source_type}:{canonical}",
            details=json.dumps({"label": label}, ensure_ascii=True),
        )
        return {"saved": True, "rating": rating, "profile": _redact_secrets(updated_profile)}

    @app.get("/api/feedback/summary")
    def get_feedback_summary(limit: int = 10) -> dict[str, Any]:
        summary_rows = timeline_store.feedback_summary()
        feedback_rows = timeline_store.list_feedback(limit=500)
        totals: dict[tuple[str, str], float] = {}
        for row in feedback_rows:
            features = _feedback_feature_rows_from_feedback_tuple(row)
            try:
                centered = max(-2.0, min(2.0, float(int(row[3]) - 3))) / 2.0
            except Exception:
                centered = 0.0
            for feature in features:
                totals[feature] = float(totals.get(feature, 0.0)) + centered
        positive = sorted(
            (
                {"feature_type": key[0], "feature_key": key[1], "weight": round(value, 3)}
                for key, value in totals.items()
                if value > 0
            ),
            key=lambda row: float(row["weight"]),
            reverse=True,
        )[: max(1, limit)]
        negative = sorted(
            (
                {"feature_type": key[0], "feature_key": key[1], "weight": round(value, 3)}
                for key, value in totals.items()
                if value < 0
            ),
            key=lambda row: float(row["weight"]),
        )[: max(1, limit)]
        return {
            "ratings": [{"rating": rating, "count": count} for rating, count in summary_rows],
            "top_positive": positive,
            "top_negative": negative,
            "recent": [
                {
                    "id": int(row[0]),
                    "run_id": str(row[1]),
                    "item_id": str(row[2]),
                    "rating": int(row[3]),
                    "label": str(row[4]),
                    "comment": str(row[5]),
                    "created_at": str(row[6]),
                }
                for row in feedback_rows[: max(1, limit)]
            ],
        }

    @app.get("/api/timeline/export")
    def get_timeline_export(
        run_id: str,
        limit_events: int = 2000,
        limit_notes: int = 500,
    ) -> dict[str, Any]:
        payload = timeline_store.export_timeline(
            run_id=run_id,
            limit_events=limit_events,
            limit_notes=limit_notes,
        )
        if not payload:
            raise HTTPException(status_code=404, detail="run timeline not found")
        payload["exported_at_utc"] = datetime.now(timezone.utc).isoformat()
        return payload

    @app.post("/api/seen/reset/preview")
    def post_seen_reset_preview(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        older_than_days = _parse_seen_reset_days(payload)
        store = SQLiteStore(settings.db_path)
        affected_count = store.preview_seen_reset(older_than_days=older_than_days)
        return {
            "scope": "older_than_days" if older_than_days is not None else "all",
            "older_than_days": older_than_days,
            "affected_count": affected_count,
        }

    @app.post("/api/seen/reset/apply")
    def post_seen_reset_apply(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        effective = load_effective_profile(
            settings.profile_path, settings.profile_overlay_path
        )
        run_policy = getattr(effective, "run_policy", None)
        guard = str(getattr(run_policy, "seen_reset_guard", "confirm")).strip().lower()
        confirmed = bool(payload.get("confirm", False))
        if guard == "confirm" and not confirmed:
            raise HTTPException(
                status_code=400,
                detail="confirm=true is required for seen reset",
            )
        older_than_days = _parse_seen_reset_days(payload)
        store = SQLiteStore(settings.db_path)
        deleted_count = store.reset_seen(older_than_days=older_than_days)
        actor = str(payload.get("actor", "web-admin") or "").strip() or "web-admin"
        store.log_admin_action(
            actor=actor,
            action="seen_reset",
            target="seen",
            details=json.dumps(
                {
                    "scope": (
                        "older_than_days"
                        if older_than_days is not None
                        else "all"
                    ),
                    "older_than_days": older_than_days,
                    "deleted_count": deleted_count,
                },
                ensure_ascii=True,
            ),
        )
        return {
            "applied": True,
            "scope": "older_than_days" if older_than_days is not None else "all",
            "older_than_days": older_than_days,
            "deleted_count": deleted_count,
        }

    @app.get("/api/source-health")
    def get_source_health() -> dict[str, Any]:
        store = SQLiteStore(settings.db_path)
        return {"items": _build_source_health_items(store)}

    @app.get("/api/source-previews")
    def get_source_previews() -> dict[str, Any]:
        store = SQLiteStore(settings.db_path)
        rows = _build_source_preview_rows(settings, store)
        return {"items": rows}

    return app


def _count_fetch_targets(sources_cfg: Any) -> int:
    total = 0
    total += len(getattr(sources_cfg, "rss_feeds", []) or [])
    total += len(getattr(sources_cfg, "youtube_channels", []) or [])
    total += len(getattr(sources_cfg, "youtube_queries", []) or [])
    total += len(getattr(sources_cfg, "x_authors", []) or [])
    total += len(getattr(sources_cfg, "x_themes", []) or [])
    if str(getattr(sources_cfg, "x_inbox_path", "") or "").strip():
        total += 1
    has_github = any(
        [
            getattr(sources_cfg, "github_repos", None),
            getattr(sources_cfg, "github_topics", None),
            getattr(sources_cfg, "github_search_queries", None),
            getattr(sources_cfg, "github_orgs", None),
        ]
    )
    if has_github:
        total += 1
    return total


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _parse_seen_reset_days(payload: dict[str, Any]) -> int | None:
    days_value = _as_int(payload.get("older_than_days"))
    if days_value is None:
        return None
    if days_value <= 0:
        return None
    return days_value


def _timeline_event_severity(stage: str, details: dict[str, Any]) -> str:
    if stage == "run_failed":
        return "error"
    status = str(details.get("status", "")).strip().lower()
    if stage == "run_finish":
        if status == "failed":
            return "error"
        if status == "partial":
            return "warn"
    error_text = str(details.get("error", "")).strip()
    if error_text:
        return "error"
    source_errors = _as_int(details.get("source_error_count"))
    summary_errors = _as_int(details.get("summary_error_count"))
    if (source_errors and source_errors > 0) or (summary_errors and summary_errors > 0):
        return "warn"
    return "info"


def _run_stage_label(stage: str) -> str:
    labels = {
        "queued": "Queued",
        "run_start": "Starting",
        "fetch_rss": "Fetching RSS",
        "fetch_youtube_channel": "Fetching YouTube Channels",
        "fetch_youtube_query": "Fetching YouTube Queries",
        "fetch_x_inbox": "Fetching X Inbox",
        "fetch_x_selectors": "Fetching X Selectors",
        "fetch_github": "Fetching GitHub",
        "normalize_filter": "Normalizing",
        "candidate_select": "Selecting Candidates",
        "score_init": "Preparing Scoring",
        "score_progress": "Scoring Items",
        "score": "Scoring Complete",
        "summarize_progress": "Summarizing",
        "summarize": "Summaries Complete",
        "quality_learning": "Applying Quality Priors",
        "quality_judge_start": "Quality Review",
        "quality_judge_result": "Quality Review Complete",
        "quality_repair_applied": "Quality Repair Applied",
        "quality_repair_skipped": "Quality Repair Skipped",
        "quality_learning_update": "Updating Quality Priors",
        "quality_repair": "Quality Repair",
        "deliver_telegram": "Delivering Telegram",
        "deliver_obsidian": "Writing Obsidian",
        "run_finish": "Finished",
        "run_failed": "Failed",
    }
    return labels.get(stage, "Processing")


def _run_stage_detail(stage: str, details: dict[str, Any], *, fallback: str) -> str:
    fetch_done = _as_int(details.get("fetch_done"))
    fetch_total = _as_int(details.get("fetch_total"))
    processed = _as_int(details.get("processed_count"))
    total = _as_int(details.get("total_count"))

    if stage in FETCH_STAGES and fetch_done is not None and fetch_total:
        return f"Collected {fetch_done}/{fetch_total} source targets."
    if stage == "score_progress" and processed is not None and total:
        return f"Scored {processed}/{total} candidates."
    if stage == "summarize_progress" and processed is not None and total:
        fallback_count = _as_int(details.get("fallback_count"))
        if fallback_count and fallback_count > 0:
            return (
                f"Summarized {processed}/{total} items "
                f"({fallback_count} fallback summaries)."
            )
        return f"Summarized {processed}/{total} items."
    if stage == "deliver_telegram":
        chunk = _as_int(details.get("chunk_index"))
        chunk_total = _as_int(details.get("chunk_count"))
        if chunk is not None and chunk_total:
            return f"Sent Telegram message chunk {chunk}/{chunk_total}."
    if stage == "run_finish":
        status = str(details.get("status", "")).strip()
        if status:
            return f"Run completed with status: {status}."
        return "Run completed."
    if stage == "run_failed":
        error = str(details.get("error", "")).strip()
        if error:
            return f"Run failed: {error}"
        return "Run failed before completion."
    return fallback


def _estimate_run_progress_percent(
    stage: str,
    *,
    details: dict[str, Any],
    fetch_done: int,
    fetch_total: int,
) -> float | None:
    if stage == "queued":
        return 1.0
    if stage == "run_start":
        return 3.0
    if stage in FETCH_STAGES:
        if fetch_total > 0:
            return 5.0 + 30.0 * (max(0, min(fetch_done, fetch_total)) / fetch_total)
        return 15.0
    if stage == "normalize_filter":
        return 38.0
    if stage == "candidate_select":
        return 42.0
    if stage == "score_init":
        return 46.0
    if stage == "score_progress":
        processed = _as_int(details.get("processed_count"))
        total = _as_int(details.get("total_count"))
        if processed is not None and total and total > 0:
            frac = max(0.0, min(1.0, processed / total))
            return 46.0 + 24.0 * frac
        return 58.0
    if stage == "score":
        return 70.0
    if stage == "summarize_progress":
        processed = _as_int(details.get("processed_count"))
        total = _as_int(details.get("total_count"))
        if processed is not None and total and total > 0:
            frac = max(0.0, min(1.0, processed / total))
            return 70.0 + 20.0 * frac
        return 82.0
    if stage == "summarize":
        return 90.0
    if stage.startswith("quality_"):
        if stage == "quality_judge_start":
            return 92.0
        if stage in {
            "quality_judge_result",
            "quality_repair_applied",
            "quality_repair_skipped",
            "quality_learning_update",
            "quality_repair",
            "quality_learning",
        }:
            return 94.0
    if stage == "deliver_telegram":
        chunk = _as_int(details.get("chunk_index"))
        chunk_total = _as_int(details.get("chunk_count"))
        if chunk is not None and chunk_total and chunk_total > 0:
            frac = max(0.0, min(1.0, chunk / chunk_total))
            return 94.0 + 3.0 * frac
        return 95.0
    if stage == "deliver_obsidian":
        return 98.0
    if stage in {"run_finish", "run_failed"}:
        return 100.0
    return None


def _save_snapshot(
    settings: WebSettings, *, action: str, details: dict[str, Any]
) -> None:
    history_dir = Path(settings.history_dir)
    history_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    snapshot_id = now.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]
    payload = {
        "id": snapshot_id,
        "created_at": now.isoformat(),
        "action": action,
        "details": details,
        "sources_overlay": _read_yaml_dict(settings.sources_overlay_path),
        "profile_overlay": _redact_secrets(
            _read_yaml_dict(settings.profile_overlay_path)
        ),
        "effective_profile": _redact_secrets(
            load_effective_profile_dict(
                settings.profile_path,
                settings.profile_overlay_path,
            )
        ),
        "effective_sources": list_sources(
            settings.sources_path,
            settings.sources_overlay_path,
        ),
    }
    path = history_dir / f"{snapshot_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _read_yaml_dict(path: str) -> dict[str, Any]:
    from yaml import safe_load

    p = Path(path)
    if not p.exists():
        return {}
    data = safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return data


def _write_yaml_dict(path: str, payload: dict[str, Any]) -> None:
    from yaml import safe_dump

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(safe_dump(payload or {}, sort_keys=False), encoding="utf-8")
    tmp.replace(p)


def _cleanup_preview_db(path: Path) -> None:
    for candidate in [
        path,
        Path(str(path) + "-wal"),
        Path(str(path) + "-shm"),
        Path(str(path) + "-journal"),
    ]:
        try:
            candidate.unlink(missing_ok=True)
        except Exception:
            continue


def _dict_diff(base: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    keys = set(base) | set(target)
    for key in keys:
        left = base.get(key)
        right = target.get(key)
        if isinstance(left, dict) and isinstance(right, dict):
            nested = _dict_diff(left, right)
            if nested:
                out[key] = nested
            continue
        if left != right:
            out[key] = right
    return out


def _build_source_health_items(store: SQLiteStore) -> list[dict[str, Any]]:
    latest_completed = store.latest_run_details(completed_only=True)
    if latest_completed is None:
        return []

    run_id, _status, started_at, errors, _summary_errors = latest_completed
    aggregate: dict[tuple[str, str], dict[str, Any]] = {}
    for raw in errors:
        parsed = _parse_source_error(raw)
        key = (parsed["kind"], parsed["source"])
        current = aggregate.get(key)
        if current is None:
            aggregate[key] = {
                "kind": parsed["kind"],
                "source": parsed["source"],
                "count": 1,
                "last_seen": started_at,
                "last_run_id": run_id,
                "last_error": parsed["error"],
                "hint": parsed["hint"],
            }
        else:
            current["count"] = int(current["count"]) + 1

    return sorted(
        aggregate.values(),
        key=lambda r: (str(r["kind"]), str(r["source"])),
    )


def _feedback_rating_for_label(label: str) -> int:
    normalized = str(label or "").strip().lower()
    mapping = {
        "more_like_this": 5,
        "prefer_source": 5,
        "not_relevant": 2,
        "too_technical": 1,
        "repeat_source": 1,
        "less_source": 2,
        "mute_source": 1,
    }
    if normalized not in mapping:
        raise HTTPException(status_code=400, detail="unsupported feedback label")
    return mapping[normalized]


def _feedback_features_for_item_feedback(
    row: dict[str, Any],
    *,
    label: str,
) -> list[tuple[str, str]]:
    features: list[tuple[str, str]] = [
        ("source", str(row.get("source_family") or "unknown").strip().lower()),
        ("source_exact", str(row.get("source") or "").strip().lower()),
        ("type", str(row.get("type") or "").strip().lower()),
    ]
    author = str(row.get("author") or "").strip().lower()
    if author:
        features.append(("author", author))
    for tag in row.get("topic_tags", []) or []:
        clean = str(tag or "").strip().lower()
        if clean:
            features.append(("topic", clean))
    for tag in row.get("format_tags", []) or []:
        clean = str(tag or "").strip().lower()
        if clean:
            features.append(("format", clean))
    if label == "repeat_source":
        features.extend(
            feature
            for feature in features
            if feature[0] in {"source", "source_exact", "author", "github_org"}
        )
    if label == "too_technical":
        features.append(("format", "technical"))
    return _dedupe_feedback_features(features)


def _feedback_features_for_source_feedback(
    *,
    source_type: str,
    source_value: str,
    label: str,
) -> list[tuple[str, str]]:
    st = str(source_type or "").strip().lower()
    value = str(source_value or "").strip().lower()
    features: list[tuple[str, str]] = []
    if st == "x_author":
        features.extend([("source", "x.com"), ("author", value)])
    elif st == "github_org":
        features.extend([("source", "github"), ("github_org", value)])
    elif st == "github_repo":
        owner = value.split("/", 1)[0].strip()
        features.extend([("source", "github"), ("source_exact", f"github:{value}")])
        if owner:
            features.append(("github_org", owner))
    elif st == "github_topic":
        features.extend([("source", "github"), ("topic", value)])
    elif st == "x_theme":
        features.append(("topic", value))
    elif st == "rss":
        parsed = urlparse(value)
        host = (parsed.netloc or "").strip().lower()
        if host.startswith("www."):
            host = host[4:]
        if host:
            features.append(("source", host))
        features.append(("source_exact", value))
    else:
        features.append(("source_exact", value))
    if label == "mute_source" and not features:
        features.append(("source_exact", value))
    return _dedupe_feedback_features(features)


def _dedupe_feedback_features(
    rows: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for feature_type, feature_key in rows:
        clean = (str(feature_type or "").strip().lower(), str(feature_key or "").strip().lower())
        if not clean[0] or not clean[1] or clean in seen:
            continue
        seen.add(clean)
        out.append(clean)
    return out


def _apply_blocked_source_preference(
    settings: WebSettings,
    *,
    source_type: str,
    source_value: str,
) -> dict[str, Any]:
    profile = load_effective_profile_dict(
        settings.profile_path,
        settings.profile_overlay_path,
    )
    source_type_key = str(source_type or "").strip().lower()
    value = str(source_value or "").strip()
    if source_type_key == "x_author":
        bucket_key = "blocked_authors_x"
    elif source_type_key == "github_org":
        bucket_key = "blocked_orgs_github"
    else:
        bucket_key = "blocked_sources"
    current = profile.get(bucket_key, [])
    rows = [str(v or "").strip() for v in current] if isinstance(current, list) else []
    if value not in rows:
        rows.append(value)
    profile[bucket_key] = rows
    save_profile_overlay(
        settings.profile_path,
        settings.profile_overlay_path,
        profile,
    )
    return load_effective_profile_dict(
        settings.profile_path,
        settings.profile_overlay_path,
    )


def _feedback_feature_rows_from_feedback_tuple(
    row: tuple[Any, ...],
) -> list[tuple[str, str]]:
    if len(row) < 10:
        return []
    raw = str(row[9] or "[]")
    try:
        payload = json.loads(raw)
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    out: list[tuple[str, str]] = []
    for entry in payload:
        if not isinstance(entry, list) or len(entry) != 2:
            continue
        feature_type = str(entry[0] or "").strip().lower()
        feature_key = str(entry[1] or "").strip().lower()
        if feature_type and feature_key:
            out.append((feature_type, feature_key))
    return out


def _build_source_preview_rows(
    settings: WebSettings,
    store: SQLiteStore,
) -> list[dict[str, Any]]:
    entries = visible_source_entries(settings.sources_path, settings.sources_overlay_path)
    health_items = _build_source_health_items(store)
    health_map = {
        (str(item["kind"]), str(item["source"])): item for item in health_items
    }
    latest_items = store.latest_items_for_sources(
        [str(entry["key"]) for entry in entries]
    )

    preview_cache: dict[str, dict[str, str]] = {}
    uncached_urls: list[str] = []
    for latest in latest_items.values():
        url = str(latest.get("url") or "").strip()
        if not url or url in preview_cache:
            continue
        cached = store.get_cached_link_preview(url, max_age_hours=24)
        if cached is not None:
            preview_cache[url] = cached
            continue
        uncached_urls.append(url)

    if uncached_urls:
        max_workers = max(1, min(6, len(uncached_urls)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(fetch_link_preview_metadata, url): url for url in uncached_urls
            }
            for future in as_completed(future_map):
                url = future_map[future]
                try:
                    preview = future.result()
                    preview_cache[url] = preview
                    store.upsert_link_preview(
                        url=url,
                        resolved_url=preview.get("resolved_url", url),
                        host=preview.get("host", ""),
                        title=preview.get("title", ""),
                        description=preview.get("description", ""),
                        image_url=preview.get("image_url", ""),
                        status=preview.get("status", "ready"),
                        error=preview.get("error", ""),
                    )
                except Exception as exc:
                    fallback_host = _host_from_url(url)
                    preview = {
                        "url": url,
                        "resolved_url": url,
                        "host": fallback_host,
                        "title": "",
                        "description": "",
                        "image_url": "",
                        "status": "error",
                        "error": str(exc),
                    }
                    preview_cache[url] = preview
                    store.upsert_link_preview(
                        url=url,
                        resolved_url=url,
                        host=fallback_host,
                        title="",
                        description="",
                        image_url="",
                        status="error",
                        error=str(exc),
                    )

    rows: list[dict[str, Any]] = []
    for entry in entries:
        source_type = str(entry["type"] or "")
        source_value = str(entry["source"] or "")
        health = health_map.get((source_type, source_value))
        latest = latest_items.get(str(entry["key"]))
        preview_url = str((latest or {}).get("url") or "").strip()
        preview_data = preview_cache.get(preview_url) if preview_url else None
        identity = _source_identity(source_type, source_value)
        latest_description = _preview_summary_fallback(latest or {})

        if latest is None:
            preview_status = "no_items"
            preview_title = "No items fetched yet"
            preview_description = identity["empty_state"]
            preview_host = identity["host_hint"]
            preview_image_url = ""
            preview_published_at = ""
        else:
            preview_status = (
                "ready"
                if preview_data and str(preview_data.get("status") or "") == "ready"
                else "preview_unavailable"
            )
            preview_title = (
                str((preview_data or {}).get("title") or "").strip()
                or str(latest.get("title") or "").strip()
                or identity["title"]
            )
            preview_description = (
                str((preview_data or {}).get("description") or "").strip()
                or latest_description
                or identity["empty_state"]
            )
            preview_host = (
                str((preview_data or {}).get("host") or "").strip()
                or _host_from_url(preview_url)
                or identity["host_hint"]
            )
            preview_image_url = str((preview_data or {}).get("image_url") or "").strip()
            preview_published_at = str(latest.get("published_at") or "").strip()

        rows.append(
            {
                "key": entry["key"],
                "type": source_type,
                "type_label": identity["type_label"],
                "source": source_value,
                "count": int((health or {}).get("count") or 0),
                "health": "failing" if health else "healthy",
                "last_error": str((health or {}).get("last_error") or "-"),
                "last_seen": str((health or {}).get("last_seen") or "-"),
                "hint": str((health or {}).get("hint") or "-"),
                "identity_title": identity["title"],
                "identity_subtitle": identity["subtitle"],
                "preview_status": preview_status,
                "preview_url": preview_url or None,
                "preview_title": preview_title,
                "preview_description": preview_description,
                "preview_image_url": preview_image_url or None,
                "preview_host": preview_host,
                "preview_published_at": preview_published_at,
                "can_edit": bool(entry["can_edit"]),
                "can_delete": bool(entry["can_delete"]),
            }
        )

    return rows


def _host_from_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    if not parsed.netloc:
        return ""
    return parsed.netloc.lower().replace("www.", "")


def _preview_summary_fallback(item: dict[str, Any]) -> str:
    preferred = str(item.get("description") or "").strip()
    if preferred:
        return preferred[:220]
    raw_text = str(item.get("raw_text") or "").strip()
    if not raw_text:
        return ""
    return raw_text[:220]


def _source_identity(source_type: str, source_value: str) -> dict[str, str]:
    st = (source_type or "").strip().lower()
    value = (source_value or "").strip()
    if st == "rss":
        host = _host_from_url(value)
        return {
            "type_label": "RSS",
            "title": host or value or "RSS feed",
            "subtitle": "Configured feed source",
            "empty_state": "This feed has not produced a stored item yet. Run the digest to populate a live preview card.",
            "host_hint": host or "rss",
        }
    if st == "youtube_channel":
        return {
            "type_label": "YouTube",
            "title": value or "YouTube channel",
            "subtitle": "Channel source",
            "empty_state": "This channel has no stored videos yet. Run the digest to generate a latest-video preview.",
            "host_hint": "youtube.com",
        }
    if st == "youtube_query":
        return {
            "type_label": "YouTube",
            "title": value or "YouTube query",
            "subtitle": "Search source",
            "empty_state": "This query has no stored video results yet. Run the digest to generate a latest-video preview.",
            "host_hint": "youtube.com",
        }
    if st == "x_author":
        return {
            "type_label": "X",
            "title": f"@{value.lstrip('@')}" if value else "X author",
            "subtitle": "Author source",
            "empty_state": "This author source has no stored posts yet. Run the digest to generate a latest-post preview.",
            "host_hint": "x.com",
        }
    if st == "x_theme":
        return {
            "type_label": "X",
            "title": value or "X theme",
            "subtitle": "Theme source",
            "empty_state": "This theme source has no stored posts yet. Run the digest to generate a latest-post preview.",
            "host_hint": "x.com",
        }
    if st == "github_repo":
        return {
            "type_label": "GitHub",
            "title": value or "GitHub repository",
            "subtitle": "Repository source",
            "empty_state": "This repository source has no stored activity yet. Run the digest to generate a latest-item preview.",
            "host_hint": "github.com",
        }
    if st == "github_topic":
        return {
            "type_label": "GitHub",
            "title": value or "GitHub topic",
            "subtitle": "Topic source",
            "empty_state": "This topic source has no stored repository activity yet. Run the digest to generate a live preview.",
            "host_hint": "github.com",
        }
    if st == "github_query":
        return {
            "type_label": "GitHub",
            "title": value or "GitHub query",
            "subtitle": "Query source",
            "empty_state": "This query source has no stored issue or PR activity yet. Run the digest to generate a live preview.",
            "host_hint": "github.com",
        }
    if st == "github_org":
        return {
            "type_label": "GitHub",
            "title": value or "GitHub organization",
            "subtitle": "Organization source",
            "empty_state": "This organization source has no stored repository activity yet. Run the digest to generate a latest-item preview.",
            "host_hint": "github.com",
        }
    if st == "x_inbox":
        return {
            "type_label": "Config",
            "title": "X inbox file",
            "subtitle": value or "Local inbox path",
            "empty_state": "This is a config-visible local inbox path, so it does not render as a remote link preview.",
            "host_hint": "local config",
        }
    return {
        "type_label": source_type or "Source",
        "title": value or "Source",
        "subtitle": "Configured source",
        "empty_state": "This source has no stored items yet.",
        "host_hint": "",
    }


def _parse_source_error(line: str) -> dict[str, str]:
    raw = (line or "").strip()
    kind = "unknown"
    source = raw
    error_text = raw

    if raw.startswith("rss:"):
        kind = "rss"
        source, error_text = _split_once(raw[len("rss:") :], ": ")
    elif raw.startswith("youtube:channel:"):
        kind = "youtube_channel"
        source, error_text = _split_once(raw[len("youtube:channel:") :], ": ")
    elif raw.startswith("youtube:query:"):
        kind = "youtube_query"
        source, error_text = _split_once(raw[len("youtube:query:") :], ": ")
    elif raw.startswith("x_inbox:"):
        kind = "x_inbox"
        source, error_text = _split_once(raw[len("x_inbox:") :], ": ")
    elif raw.startswith("x_author:"):
        kind = "x_author"
        source, error_text = _split_once(raw[len("x_author:") :], ": ")
    elif raw.startswith("x_theme:"):
        kind = "x_theme"
        source, error_text = _split_once(raw[len("x_theme:") :], ": ")
    elif raw.startswith("github:"):
        kind = "github"
        error_text = raw[len("github:") :].strip()
        source = "github"
        m = re.search(r"\(/repos/[^\)]+\)", error_text)
        if m:
            source = m.group(0).strip("()")

    return {
        "kind": kind,
        "source": source or "unknown",
        "error": error_text,
        "hint": _error_hint(kind, error_text),
    }


def _split_once(value: str, marker: str) -> tuple[str, str]:
    if marker not in value:
        return value, ""
    left, right = value.split(marker, 1)
    return left.strip(), right.strip()


def _error_hint(kind: str, error_text: str) -> str:
    text = (error_text or "").lower()
    if kind == "rss":
        return "Feed may be unavailable or invalid. Open URL in browser and verify it still publishes RSS/Atom."
    if kind.startswith("youtube"):
        return "YouTube source may be invalid/rate-limited. Verify channel/query and retry."
    if kind == "x_inbox":
        return "Inbox file path/content issue. Check x_inbox_path and file permissions."
    if kind == "x_author":
        return (
            "X author selector fetch failed. Verify DIGEST_X_PROVIDER=x_api, X_BEARER_TOKEN, recent-search access, and selector handle."
        )
    if kind == "x_theme":
        return (
            "X theme selector fetch failed. Verify provider auth, query syntax, and recent-search access or rate limits."
        )
    if kind == "github" and "httperror: 403" in text:
        return (
            "GitHub API rate limit/auth issue. Set or refresh GITHUB_TOKEN and re-run."
        )
    if "timed out" in text or "connection" in text or "temporary failure" in text:
        return "Network/connectivity issue. Check internet or retry later."
    return "Inspect source settings and logs; then retry the run."
