"""Run-mode resolution helpers for the web control plane.

These are pure functions and configuration extracted from ``digest.web.app``;
they map run-mode names to ingestion/selection options and hold no route or
application state.
"""

from __future__ import annotations

from typing import Any

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
