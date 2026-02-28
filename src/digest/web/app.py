from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import uuid
from typing import Any

from digest.config import parse_profile_dict, profile_to_dict
from digest.logging_utils import get_run_logger
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


def create_app(settings: WebSettings):
    try:
        from fastapi import FastAPI, HTTPException
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

    class SourceMutation(BaseModel):
        source_type: str
        value: str

    class ProfilePayload(BaseModel):
        profile: dict[str, Any]

    class RollbackPayload(BaseModel):
        snapshot_id: str

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
    def post_source_add(payload: SourceMutation) -> dict[str, Any]:
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
        return {"created": created, "canonical": canonical}

    @app.post("/api/config/sources/remove")
    def post_source_remove(payload: SourceMutation) -> dict[str, Any]:
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
        return {"removed": removed, "canonical": canonical}

    @app.get("/api/config/profile")
    def get_profile() -> dict[str, Any]:
        effective = load_effective_profile(
            settings.profile_path, settings.profile_overlay_path
        )
        return {"profile": profile_to_dict(effective)}

    @app.post("/api/config/profile/validate")
    def post_profile_validate(payload: ProfilePayload) -> dict[str, Any]:
        validated = parse_profile_dict(payload.profile)
        return {"valid": True, "profile": profile_to_dict(validated)}

    @app.post("/api/config/profile/diff")
    def post_profile_diff(payload: ProfilePayload) -> dict[str, Any]:
        validated = parse_profile_dict(payload.profile)
        candidate = profile_to_dict(validated)
        current = profile_to_dict(
            load_effective_profile(settings.profile_path, settings.profile_overlay_path)
        )
        return {
            "diff": _dict_diff(current, candidate),
        }

    @app.post("/api/config/profile/save")
    def post_profile_save(payload: ProfilePayload) -> dict[str, Any]:
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
    def post_rollback(payload: RollbackPayload) -> dict[str, Any]:
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

    @app.post("/api/run-now")
    def post_run_now() -> dict[str, Any]:
        run_request_id = uuid.uuid4().hex[:12]
        acquired, current = lock.acquire(run_request_id)
        if not acquired and current is not None:
            return {
                "started": False,
                "active_run_id": current.run_id,
                "started_at": current.started_at,
            }

        def worker() -> None:
            try:
                sources = load_effective_sources(
                    settings.sources_path,
                    settings.sources_overlay_path,
                )
                profile = load_effective_profile(
                    settings.profile_path,
                    settings.profile_overlay_path,
                )
                store = SQLiteStore(settings.db_path)
                run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                    logger=get_run_logger(run_request_id),
                )
            finally:
                lock.release(run_request_id)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return {"started": True, "run_id": run_request_id}

    @app.get("/api/run-status")
    def get_run_status() -> dict[str, Any]:
        store = SQLiteStore(settings.db_path)
        latest = store.latest_run_summary()
        active = lock.current()
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
                    "source_errors": latest[3],
                    "summary_errors": latest[4],
                }
                if latest is not None
                else None
            ),
        }

    return app


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
