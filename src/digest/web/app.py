from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import threading
import uuid
from typing import Any

from digest.config import parse_profile_dict, profile_to_dict
from digest.logging_utils import get_run_logger
from digest.ops.onboarding import (
    OnboardingSettings,
    apply_source_pack,
    build_onboarding_status,
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
    list_sources,
    load_effective_sources,
    remove_source,
    supported_source_types,
)
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore


FETCH_STAGES = {
    "fetch_rss",
    "fetch_youtube_channel",
    "fetch_youtube_query",
    "fetch_x_inbox",
    "fetch_github",
}


def _web_live_run_options(*, trigger: str) -> dict[str, bool]:
    if trigger == "web":
        return {
            "use_last_completed_window": True,
            "only_new": True,
            "allow_seen_fallback": False,
        }
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
    run_lock_stale_seconds: int = 21600
    history_dir: str = ".runtime/config-history"
    onboarding_state_path: str = ".runtime/onboarding-state.json"


def create_app(settings: WebSettings):
    try:
        from fastapi import Body, FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "FastAPI and pydantic are required for web mode. Install optional web deps."
        ) from exc

    app = FastAPI(title="Digest Config Console API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:4173",
            "http://localhost:4173",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    lock = RunLock(
        settings.run_lock_path, stale_seconds=settings.run_lock_stale_seconds
    )

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

    def _remember_progress_run(run_id: str) -> None:
        nonlocal latest_progress_run_id
        if run_id in run_progress_order:
            run_progress_order.remove(run_id)
        run_progress_order.append(run_id)
        latest_progress_run_id = run_id
        while len(run_progress_order) > 40:
            stale = run_progress_order.pop(0)
            run_progress.pop(stale, None)

    def _init_run_progress(*, run_id: str, mode: str) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        with progress_lock:
            _remember_progress_run(run_id)
            run_progress[run_id] = {
                "run_id": run_id,
                "pipeline_run_id": "",
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

        with progress_lock:
            state = run_progress.get(run_id)
            if state is None:
                return

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
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "details": details,
                    "event_index": int(state.get("event_index", 0) or 0) + 1,
                }
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
        with progress_lock:
            state = run_progress.get(run_id)
            if state is None:
                return
            details = dict(state.get("details", {}))
            if error:
                details["error"] = error
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
                    "event_index": int(state.get("event_index", 0) or 0) + 1,
                }
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

    class SourceMutation(BaseModel):
        source_type: str
        value: str

    class ProfilePayload(BaseModel):
        profile: dict[str, Any]

    class RollbackPayload(BaseModel):
        snapshot_id: str

    class SourcePackPayload(BaseModel):
        pack_id: str

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
    def post_source_add(payload: SourceMutation = Body(...)) -> dict[str, Any]:
        created, canonical = add_source(
            settings.sources_path,
            settings.sources_overlay_path,
            payload.source_type,
            payload.value,
        )
        _save_snapshot(
            settings,
            action="source_add",
            details={"source_type": payload.source_type, "value": canonical},
        )
        mark_step_completed(
            settings.onboarding_state_path,
            "sources",
            details=f"{payload.source_type}:{canonical}",
        )
        return {"created": created, "canonical": canonical}

    @app.post("/api/config/sources/remove")
    def post_source_remove(payload: SourceMutation = Body(...)) -> dict[str, Any]:
        removed, canonical = remove_source(
            settings.sources_path,
            settings.sources_overlay_path,
            payload.source_type,
            payload.value,
        )
        _save_snapshot(
            settings,
            action="source_remove",
            details={"source_type": payload.source_type, "value": canonical},
        )
        mark_step_completed(
            settings.onboarding_state_path,
            "sources",
            details=f"{payload.source_type}:{canonical}",
        )
        return {"removed": removed, "canonical": canonical}

    @app.get("/api/config/profile")
    def get_profile() -> dict[str, Any]:
        effective = load_effective_profile(
            settings.profile_path, settings.profile_overlay_path
        )
        return {"profile": profile_to_dict(effective)}

    @app.post("/api/config/profile/validate")
    def post_profile_validate(payload: ProfilePayload = Body(...)) -> dict[str, Any]:
        validated = parse_profile_dict(payload.profile)
        return {"valid": True, "profile": profile_to_dict(validated)}

    @app.post("/api/config/profile/diff")
    def post_profile_diff(payload: ProfilePayload = Body(...)) -> dict[str, Any]:
        validated = parse_profile_dict(payload.profile)
        candidate = profile_to_dict(validated)
        current = profile_to_dict(
            load_effective_profile(settings.profile_path, settings.profile_overlay_path)
        )
        return {
            "diff": _dict_diff(current, candidate),
        }

    @app.post("/api/config/profile/save")
    def post_profile_save(payload: ProfilePayload = Body(...)) -> dict[str, Any]:
        overlay = save_profile_overlay(
            settings.profile_path,
            settings.profile_overlay_path,
            payload.profile,
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
        return {"saved": True, "overlay": overlay}

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
                "github_repo": list(sources_cfg.github_repos),
                "github_topic": list(sources_cfg.github_topics),
                "github_query": list(sources_cfg.github_search_queries),
                "github_org": list(sources_cfg.github_orgs),
                "x_inbox": [sources_cfg.x_inbox_path]
                if sources_cfg.x_inbox_path
                else [],
            },
            "profile": profile_to_dict(profile_cfg),
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
    def post_rollback(payload: RollbackPayload = Body(...)) -> dict[str, Any]:
        path = Path(settings.history_dir) / f"{payload.snapshot_id}.json"
        if not path.exists():
            raise HTTPException(status_code=404, detail="snapshot not found")
        data = json.loads(path.read_text(encoding="utf-8"))
        sources_overlay = data.get("sources_overlay", {})
        profile_overlay = data.get("profile_overlay", {})
        _write_yaml_dict(settings.sources_overlay_path, sources_overlay)
        _write_yaml_dict(settings.profile_overlay_path, profile_overlay)
        _save_snapshot(
            settings, action="rollback", details={"snapshot_id": payload.snapshot_id}
        )
        return {"rolled_back": True}

    def _start_live_run() -> dict[str, Any]:
        run_request_id = uuid.uuid4().hex[:12]
        acquired, current = lock.acquire(run_request_id)
        if not acquired and current is not None:
            return {
                "started": False,
                "active_run_id": current.run_id,
                "started_at": current.started_at,
            }

        _init_run_progress(run_id=run_request_id, mode="live")

        def worker() -> None:
            worker_logger = get_run_logger(run_request_id)
            try:
                sources = load_effective_sources(
                    settings.sources_path,
                    settings.sources_overlay_path,
                )
                _set_fetch_plan(run_request_id, sources)
                profile = load_effective_profile(
                    settings.profile_path,
                    settings.profile_overlay_path,
                )
                store = SQLiteStore(settings.db_path)
                run_digest(
                    sources,
                    profile,
                    store,
                    **_web_live_run_options(trigger="web"),
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
        return {"started": True, "run_id": run_request_id}

    @app.post("/api/run-now")
    def post_run_now() -> dict[str, Any]:
        return _start_live_run()

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
        payload: SourcePackPayload = Body(...),
    ) -> dict[str, Any]:
        try:
            result = apply_source_pack(onboarding_settings, payload.pack_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        _save_snapshot(
            settings,
            action="source_pack_apply",
            details={
                "pack_id": payload.pack_id,
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
                details=f"pack:{payload.pack_id}",
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

    @app.get("/api/source-health")
    def get_source_health() -> dict[str, Any]:
        store = SQLiteStore(settings.db_path)
        rows = store.recent_source_error_runs(limit=20)
        aggregate: dict[tuple[str, str], dict[str, Any]] = {}
        for run_id, started_at, errors in rows:
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

        items = sorted(
            aggregate.values(),
            key=lambda r: (int(r["count"]), str(r["last_seen"])),
            reverse=True,
        )
        return {"items": items}

    return app


def _count_fetch_targets(sources_cfg: Any) -> int:
    total = 0
    total += len(getattr(sources_cfg, "rss_feeds", []) or [])
    total += len(getattr(sources_cfg, "youtube_channels", []) or [])
    total += len(getattr(sources_cfg, "youtube_queries", []) or [])
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


def _run_stage_label(stage: str) -> str:
    labels = {
        "queued": "Queued",
        "run_start": "Starting",
        "fetch_rss": "Fetching RSS",
        "fetch_youtube_channel": "Fetching YouTube Channels",
        "fetch_youtube_query": "Fetching YouTube Queries",
        "fetch_x_inbox": "Fetching X Inbox",
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
        "profile_overlay": _read_yaml_dict(settings.profile_overlay_path),
        "effective_profile": load_effective_profile_dict(
            settings.profile_path,
            settings.profile_overlay_path,
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
    if kind == "github" and "httperror: 403" in text:
        return (
            "GitHub API rate limit/auth issue. Set or refresh GITHUB_TOKEN and re-run."
        )
    if "timed out" in text or "connection" in text or "temporary failure" in text:
        return "Network/connectivity issue. Check internet or retry later."
    return "Inspect source settings and logs; then retry the run."
