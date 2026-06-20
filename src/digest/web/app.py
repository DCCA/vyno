from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import uuid
from typing import Any

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
    supported_source_types,
)
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore
from digest.web.feedback import (
    _feedback_feature_rows_from_feedback_tuple,
    _feedback_features_for_item_feedback,
    _feedback_features_for_source_feedback,
    _feedback_rating_for_label,
)
from digest.web.run_progress import (
    FETCH_STAGES,
    _as_int,
    _count_fetch_targets,
    _estimate_run_progress_percent,
    _run_stage_detail,
    _run_stage_label,
    _timeline_event_severity,
)
from digest.web.schedule import (
    _next_allowed_schedule_slot_utc,
    _schedule_completion_detail,
    _schedule_config_from_profile,
    _schedule_due_slot_utc,
    _schedule_status_payload,
)
from digest.web.security import (
    _api_auth_decision,
    _cors_allow_origin_regex,
    _cors_allowed_origins,
    _redact_secrets,
    _rehydrate_redacted_value,
    _web_api_auth_mode,
    _web_api_token,
    _web_api_token_header,
)
from digest.web.sources import (
    _apply_blocked_source_preference,
    _build_source_health_items,
    _build_source_preview_rows,
    _parse_source_error,
)


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


def create_app(settings: WebSettings):
    try:
        from fastapi import Body, FastAPI, HTTPException, Request
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "FastAPI and pydantic are required for web mode. Install optional web deps."
        ) from exc

    @asynccontextmanager
    async def _lifespan(app: FastAPI):
        start = getattr(app.state, "start_scheduler", None)
        if start is not None:
            start()
        try:
            yield
        finally:
            stop = getattr(app.state, "stop_scheduler", None)
            if stop is not None:
                stop()

    app = FastAPI(
        title="Digest Config Console API",
        version="0.1.0",
        lifespan=_lifespan,
    )
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
        # Snapshot the current state BEFORE overwriting so a rollback is undoable.
        _save_snapshot(
            settings, action="pre_rollback", details={"target_snapshot_id": snapshot_id}
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

    def _start_scheduler() -> None:
        schedule_stop_event.clear()
        thread = threading.Thread(target=_scheduler_loop, daemon=True)
        thread.start()
        app.state.schedule_thread = thread

    def _stop_scheduler() -> None:
        schedule_stop_event.set()

    app.state.start_scheduler = _start_scheduler
    app.state.stop_scheduler = _stop_scheduler

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
        try:
            rating = _feedback_rating_for_label(label)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
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
        try:
            rating = _feedback_rating_for_label(label)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
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

    # ── Serve built frontend (production) ────────────────────────────
    _static_dir = Path("web/dist")
    if not _static_dir.is_dir():
        _static_dir = Path(__file__).resolve().parent.parent.parent.parent / "web" / "dist"
    if _static_dir.is_dir():
        from fastapi.responses import FileResponse

        _index_html = _static_dir / "index.html"

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str) -> Any:
            file_path = _static_dir / full_path
            if full_path and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(_index_html)

    return app


def _parse_seen_reset_days(payload: dict[str, Any]) -> int | None:
    days_value = _as_int(payload.get("older_than_days"))
    if days_value is None:
        return None
    if days_value <= 0:
        return None
    return days_value


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
