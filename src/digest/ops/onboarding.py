from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
from typing import Any

import yaml

from digest.ops.profile_registry import load_effective_profile
from digest.ops.source_registry import add_source, load_effective_sources
from digest.storage.sqlite_store import SQLiteStore


@dataclass(slots=True)
class OnboardingSettings:
    sources_path: str
    sources_overlay_path: str
    profile_path: str
    profile_overlay_path: str
    db_path: str
    run_lock_path: str = ".runtime/run.lock"
    history_dir: str = ".runtime/config-history"
    onboarding_state_path: str = ".runtime/onboarding-state.json"


ONBOARDING_STEPS: list[tuple[str, str]] = [
    ("preflight", "Run preflight checks"),
    ("outputs", "Connect outputs (Telegram or Obsidian)"),
    ("sources", "Choose starter sources"),
    ("profile", "Tune profile basics"),
    ("preview", "Run preview digest"),
    ("activate", "Activate live run"),
    ("health", "Confirm run health"),
]


_SOURCE_PACKS: list[dict[str, Any]] = [
    {
        "id": "quickstart-core",
        "name": "Quickstart Core",
        "description": "Balanced starter pack for first useful digest runs.",
        "entries": [
            ("rss", "https://openai.com/news/rss.xml"),
            ("rss", "https://arxiv.org/rss/cs.AI"),
            ("rss", "https://blog.google/technology/ai/rss/"),
            ("youtube_channel", "UCMLtBahI5DMrt0NPvDSoIRQ"),
            ("youtube_channel", "UCXUPKJO5MZQN11PqgIvyuvQ"),
            ("github_repo", "openai/openai-cookbook"),
            ("github_org", "https://github.com/vercel-labs"),
        ],
    },
    {
        "id": "ai-engineering",
        "name": "AI Engineering",
        "description": "Builder-focused channels and GitHub sources.",
        "entries": [
            ("youtube_channel", "UCmOwsoHty5PrmE-3QhUBfPQ"),
            ("youtube_channel", "UCFbNIlppjAuEX4znoulh0Cw"),
            ("github_repo", "anthropics/claude-code"),
            ("github_topic", "llm"),
            ("github_query", "is:issue llm"),
        ],
    },
    {
        "id": "research-signals",
        "name": "Research Signals",
        "description": "Research-heavy feeds and technical video sources.",
        "entries": [
            ("rss", "https://arxiv.org/rss/cs.LG"),
            ("rss", "https://arxiv.org/rss/cs.CL"),
            ("rss", "https://news.mit.edu/rss/topic/artificial-intelligence2"),
            ("youtube_channel", "UCbfYPyITQ-7l4upoX8nvctg"),
            ("youtube_channel", "UCv83tO5cePwHMt1952IVVHw"),
        ],
    },
]


def run_preflight(
    settings: OnboardingSettings,
    *,
    check_network: bool = True,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add_check(
        check_id: str,
        label: str,
        status: str,
        detail: str,
        *,
        hint: str = "",
        required: bool = True,
    ) -> None:
        checks.append(
            {
                "id": check_id,
                "label": label,
                "status": status,
                "detail": detail,
                "hint": hint,
                "required": required,
            }
        )

    sources_cfg = None
    profile_cfg = None

    try:
        sources_cfg = load_effective_sources(
            settings.sources_path,
            settings.sources_overlay_path,
        )
        add_check(
            "sources_load",
            "Load effective sources",
            "pass",
            "Base + overlay sources parsed successfully.",
        )
    except Exception as exc:
        add_check(
            "sources_load",
            "Load effective sources",
            "fail",
            f"Failed to parse sources: {exc}",
            hint="Fix config/sources.yaml and data/sources.local.yaml syntax/content.",
        )

    try:
        profile_cfg = load_effective_profile(
            settings.profile_path,
            settings.profile_overlay_path,
        )
        add_check(
            "profile_load",
            "Load effective profile",
            "pass",
            "Base + overlay profile parsed successfully.",
        )
    except Exception as exc:
        add_check(
            "profile_load",
            "Load effective profile",
            "fail",
            f"Failed to parse profile: {exc}",
            hint="Fix config/profile.yaml and data/profile.local.yaml syntax/content.",
        )

    for check_id, label, path_value in [
        (
            "sources_overlay_writable",
            "Sources overlay writable",
            settings.sources_overlay_path,
        ),
        (
            "profile_overlay_writable",
            "Profile overlay writable",
            settings.profile_overlay_path,
        ),
        ("db_writable", "Digest DB writable", settings.db_path),
        (
            "run_lock_writable",
            "Run lock path writable",
            settings.run_lock_path,
        ),
        (
            "history_writable",
            "History path writable",
            settings.history_dir,
        ),
        (
            "onboarding_state_writable",
            "Onboarding state path writable",
            settings.onboarding_state_path,
        ),
    ]:
        ok, detail = _check_write_target(path_value)
        add_check(
            check_id,
            label,
            "pass" if ok else "fail",
            detail,
            hint=(
                "Fix directory permissions or choose a writable path." if not ok else ""
            ),
        )

    needs_openai = False
    if profile_cfg is not None:
        needs_openai = bool(
            profile_cfg.llm_enabled
            or profile_cfg.agent_scoring_enabled
            or profile_cfg.quality_repair_enabled
        )
    has_openai_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
    if needs_openai and not has_openai_key:
        add_check(
            "openai_key",
            "OPENAI_API_KEY present",
            "fail",
            "OpenAI key is required by current profile settings.",
            hint="Set OPENAI_API_KEY in .env or environment before activation.",
        )
    elif needs_openai:
        add_check(
            "openai_key",
            "OPENAI_API_KEY present",
            "pass",
            "OpenAI key detected.",
        )
    else:
        add_check(
            "openai_key",
            "OPENAI_API_KEY present",
            "pass",
            "OpenAI key not required by current profile settings.",
            required=False,
        )

    github_enabled = False
    if sources_cfg is not None:
        github_enabled = bool(
            sources_cfg.github_repos
            or sources_cfg.github_topics
            or sources_cfg.github_search_queries
            or sources_cfg.github_orgs
        )
    has_github_token = bool(os.getenv("GITHUB_TOKEN", "").strip())
    if github_enabled and not has_github_token:
        add_check(
            "github_token",
            "GITHUB_TOKEN for GitHub sources",
            "warn",
            "GitHub sources are configured without GITHUB_TOKEN.",
            hint="Set GITHUB_TOKEN to reduce API rate-limit failures.",
            required=False,
        )
    elif github_enabled:
        add_check(
            "github_token",
            "GITHUB_TOKEN for GitHub sources",
            "pass",
            "GitHub token detected.",
            required=False,
        )
    else:
        add_check(
            "github_token",
            "GITHUB_TOKEN for GitHub sources",
            "pass",
            "GitHub selectors are not configured.",
            required=False,
        )

    telegram_ready = False
    obsidian_ready = False
    if profile_cfg is not None:
        telegram_ready = bool(
            profile_cfg.output.telegram_bot_token
            and profile_cfg.output.telegram_chat_id
        )
        if profile_cfg.output.obsidian_vault_path:
            ok, detail = _check_directory_target(profile_cfg.output.obsidian_vault_path)
            obsidian_ready = ok
            add_check(
                "obsidian_target",
                "Obsidian vault path",
                "pass" if ok else "warn",
                detail,
                hint=(
                    "Set output.obsidian_vault_path to an existing/writable directory."
                    if not ok
                    else ""
                ),
                required=False,
            )
        else:
            add_check(
                "obsidian_target",
                "Obsidian vault path",
                "warn",
                "No Obsidian output path configured.",
                hint="Set output.obsidian_vault_path in profile or OBSIDIAN_VAULT_PATH env.",
                required=False,
            )

    if telegram_ready or obsidian_ready:
        mode = []
        if telegram_ready:
            mode.append("telegram")
        if obsidian_ready:
            mode.append("obsidian")
        add_check(
            "outputs_ready",
            "Output targets ready",
            "pass",
            f"Configured outputs: {', '.join(mode)}.",
            required=False,
        )
    else:
        add_check(
            "outputs_ready",
            "Output targets ready",
            "warn",
            "No ready output target detected.",
            hint="Configure Telegram credentials and/or Obsidian vault path before activation.",
            required=False,
        )

    if sources_cfg is not None and sources_cfg.x_inbox_path:
        inbox_path = Path(sources_cfg.x_inbox_path).expanduser()
        if inbox_path.exists() and inbox_path.is_file():
            add_check(
                "x_inbox",
                "X inbox file",
                "pass",
                f"X inbox file found: {inbox_path}",
                required=False,
            )
        else:
            add_check(
                "x_inbox",
                "X inbox file",
                "warn",
                f"X inbox file not found: {inbox_path}",
                hint="Create data/x_inbox.txt or remove x_inbox_path if not needed.",
                required=False,
            )

    if check_network:
        host_checks: list[tuple[str, str]] = []
        if needs_openai:
            host_checks.append(("dns_openai", "api.openai.com"))
        if github_enabled:
            host_checks.append(("dns_github", "api.github.com"))
        if telegram_ready:
            host_checks.append(("dns_telegram", "api.telegram.org"))

        if not host_checks:
            add_check(
                "dns_checks",
                "Provider DNS checks",
                "pass",
                "No provider DNS checks required for current setup.",
                required=False,
            )
        else:
            for check_id, host in host_checks:
                resolved = _can_resolve_host(host)
                add_check(
                    check_id,
                    f"DNS resolution ({host})",
                    "pass" if resolved else "warn",
                    (f"Resolved {host}." if resolved else f"Could not resolve {host}."),
                    hint=(
                        "Check network/DNS settings before activation."
                        if not resolved
                        else ""
                    ),
                    required=False,
                )

    pass_count = sum(1 for c in checks if c["status"] == "pass")
    warn_count = sum(1 for c in checks if c["status"] == "warn")
    fail_count = sum(1 for c in checks if c["status"] == "fail")

    source_count = 0
    if sources_cfg is not None:
        source_count += len(sources_cfg.rss_feeds)
        source_count += len(sources_cfg.youtube_channels)
        source_count += len(sources_cfg.youtube_queries)
        source_count += len(sources_cfg.x_authors)
        source_count += len(sources_cfg.x_themes)
        source_count += len(sources_cfg.github_repos)
        source_count += len(sources_cfg.github_topics)
        source_count += len(sources_cfg.github_search_queries)
        source_count += len(sources_cfg.github_orgs)
        source_count += 1 if sources_cfg.x_inbox_path else 0

    return {
        "generated_at_utc": _now_iso(),
        "ok": fail_count == 0,
        "pass_count": pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "checks": checks,
        "derived": {
            "telegram_ready": telegram_ready,
            "obsidian_ready": obsidian_ready,
            "outputs_ready": telegram_ready or obsidian_ready,
            "source_count": source_count,
            "needs_openai": needs_openai,
            "github_enabled": github_enabled,
        },
    }


def list_source_packs() -> list[dict[str, Any]]:
    packs: list[dict[str, Any]] = []
    for pack in _SOURCE_PACKS:
        rows = pack["entries"]
        packs.append(
            {
                "id": str(pack["id"]),
                "name": str(pack["name"]),
                "description": str(pack["description"]),
                "item_count": len(rows),
                "entries": [
                    {"source_type": source_type, "value": value}
                    for source_type, value in rows
                ],
            }
        )
    return packs


def apply_source_pack(settings: OnboardingSettings, pack_id: str) -> dict[str, Any]:
    pack = _source_pack_by_id(pack_id)
    if pack is None:
        raise ValueError(f"Unknown source pack: {pack_id}")

    added: list[dict[str, str]] = []
    existing: list[dict[str, str]] = []
    errors: list[str] = []

    for source_type, value in pack["entries"]:
        try:
            created, canonical = add_source(
                settings.sources_path,
                settings.sources_overlay_path,
                source_type,
                value,
            )
        except Exception as exc:
            errors.append(f"{source_type}:{value}: {exc}")
            continue

        row = {"source_type": source_type, "value": canonical}
        if created:
            added.append(row)
        else:
            existing.append(row)

    return {
        "pack_id": str(pack["id"]),
        "pack_name": str(pack["name"]),
        "added": added,
        "existing": existing,
        "errors": errors,
        "added_count": len(added),
        "existing_count": len(existing),
        "error_count": len(errors),
    }


def load_onboarding_state(path: str) -> dict[str, Any]:
    state_path = Path(path)
    if not state_path.exists():
        return {"steps": {}, "updated_at": ""}
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {"steps": {}, "updated_at": ""}
    if not isinstance(payload, dict):
        return {"steps": {}, "updated_at": ""}

    steps_raw = payload.get("steps")
    steps: dict[str, dict[str, Any]] = {}
    if isinstance(steps_raw, dict):
        for key, value in steps_raw.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                continue
            steps[key] = {
                "completed": bool(value.get("completed", False)),
                "completed_at": str(value.get("completed_at", "") or ""),
                "details": str(value.get("details", "") or ""),
            }

    return {
        "steps": steps,
        "updated_at": str(payload.get("updated_at", "") or ""),
    }


def mark_step_completed(
    path: str, step_id: str, *, details: str = ""
) -> dict[str, Any]:
    state = load_onboarding_state(path)
    steps = state.setdefault("steps", {})
    row = steps.get(step_id)
    if not isinstance(row, dict):
        row = {}
    already_completed = bool(row.get("completed", False))
    existing_details = str(row.get("details", "") or "")
    if already_completed and (not details or details == existing_details):
        return state

    row["completed"] = True
    if not already_completed:
        row["completed_at"] = _now_iso()
    elif not str(row.get("completed_at", "") or ""):
        row["completed_at"] = _now_iso()
    if details:
        row["details"] = details
    steps[step_id] = row
    state["updated_at"] = _now_iso()
    _write_json_atomic(path, state)
    return state


def build_onboarding_status(settings: OnboardingSettings) -> dict[str, Any]:
    preflight = run_preflight(settings, check_network=False)
    state = load_onboarding_state(settings.onboarding_state_path)
    step_state = state.get("steps", {}) if isinstance(state.get("steps"), dict) else {}

    latest_completed_payload: dict[str, Any] | None = None
    try:
        store = SQLiteStore(settings.db_path)
        latest = store.latest_run_details(completed_only=True)
        if latest is not None:
            latest_completed_payload = {
                "run_id": latest[0],
                "status": latest[1],
                "started_at": latest[2],
                "source_error_count": len(latest[3]),
                "summary_error_count": len(latest[4]),
            }
    except Exception:
        latest_completed_payload = None

    profile_overlay = _read_yaml_dict(settings.profile_overlay_path)
    sources_total = int(preflight.get("derived", {}).get("source_count", 0) or 0)
    outputs_ready = bool(preflight.get("derived", {}).get("outputs_ready", False))

    def step_completed(step_id: str, derived: bool = False) -> tuple[bool, str]:
        entry = step_state.get(step_id)
        if isinstance(entry, dict) and bool(entry.get("completed", False)):
            return True, str(entry.get("completed_at", "") or "")
        return derived, ""

    step_rows: list[dict[str, Any]] = []

    completed, completed_at = step_completed(
        "preflight", bool(preflight.get("ok", False))
    )
    step_rows.append(
        {
            "id": "preflight",
            "label": "Run preflight checks",
            "status": "complete" if completed else "pending",
            "completed_at": completed_at,
            "detail": (
                f"{preflight['pass_count']} pass, {preflight['warn_count']} warn, {preflight['fail_count']} fail"
            ),
        }
    )

    completed, completed_at = step_completed("outputs", outputs_ready)
    step_rows.append(
        {
            "id": "outputs",
            "label": "Connect outputs (Telegram or Obsidian)",
            "status": "complete" if completed else "pending",
            "completed_at": completed_at,
            "detail": (
                "At least one output target is ready."
                if outputs_ready
                else "No ready output target detected."
            ),
        }
    )

    completed, completed_at = step_completed("sources", sources_total > 0)
    step_rows.append(
        {
            "id": "sources",
            "label": "Choose starter sources",
            "status": "complete" if completed else "pending",
            "completed_at": completed_at,
            "detail": f"{sources_total} source selectors configured.",
        }
    )

    completed, completed_at = step_completed("profile", bool(profile_overlay))
    step_rows.append(
        {
            "id": "profile",
            "label": "Tune profile basics",
            "status": "complete" if completed else "pending",
            "completed_at": completed_at,
            "detail": (
                f"Profile overlay keys: {', '.join(sorted(profile_overlay.keys()))}"
                if profile_overlay
                else "Profile overlay has no local overrides yet."
            ),
        }
    )

    completed, completed_at = step_completed("preview", False)
    step_rows.append(
        {
            "id": "preview",
            "label": "Run preview digest",
            "status": "complete" if completed else "pending",
            "completed_at": completed_at,
            "detail": "Generate a non-delivering preview before activation.",
        }
    )

    completed, completed_at = step_completed(
        "activate", latest_completed_payload is not None
    )
    step_rows.append(
        {
            "id": "activate",
            "label": "Activate live run",
            "status": "complete" if completed else "pending",
            "completed_at": completed_at,
            "detail": (
                f"Latest completed run: {latest_completed_payload['run_id']}"
                if latest_completed_payload is not None
                else "No completed live run detected yet."
            ),
        }
    )

    health_ready = (
        latest_completed_payload is not None
        and latest_completed_payload.get("status") in {"success", "partial"}
    )
    completed, completed_at = step_completed("health", health_ready)
    step_rows.append(
        {
            "id": "health",
            "label": "Confirm run health",
            "status": "complete" if completed else "pending",
            "completed_at": completed_at,
            "detail": (
                (
                    f"Last run status={latest_completed_payload['status']} "
                    f"source_errors={latest_completed_payload['source_error_count']} "
                    f"summary_errors={latest_completed_payload['summary_error_count']}"
                )
                if latest_completed_payload is not None
                else "Run health unavailable until first completed run."
            ),
        }
    )

    complete_count = sum(1 for row in step_rows if row["status"] == "complete")

    return {
        "generated_at_utc": _now_iso(),
        "steps": step_rows,
        "progress": {"completed": complete_count, "total": len(step_rows)},
        "preflight": {
            "ok": bool(preflight.get("ok", False)),
            "pass_count": int(preflight.get("pass_count", 0)),
            "warn_count": int(preflight.get("warn_count", 0)),
            "fail_count": int(preflight.get("fail_count", 0)),
        },
        "latest_completed": latest_completed_payload,
    }


def _source_pack_by_id(pack_id: str) -> dict[str, Any] | None:
    target = (pack_id or "").strip().lower()
    if not target:
        return None
    for pack in _SOURCE_PACKS:
        if str(pack.get("id", "")).strip().lower() == target:
            return pack
    return None


def _check_write_target(raw_path: str) -> tuple[bool, str]:
    path = Path(raw_path)
    if path.exists():
        if path.is_dir():
            writable = os.access(path, os.W_OK)
            return writable, (
                f"Directory is {'writable' if writable else 'not writable'}: {path}"
            )
        writable = os.access(path, os.W_OK)
        return writable, f"File is {'writable' if writable else 'not writable'}: {path}"

    anchor = path.parent
    while not anchor.exists() and anchor != anchor.parent:
        anchor = anchor.parent
    if not anchor.exists():
        return False, f"No existing parent directory found for: {path}"

    writable = os.access(anchor, os.W_OK)
    return writable, (
        f"Parent directory is {'writable' if writable else 'not writable'}: {anchor}"
    )


def _check_directory_target(raw_path: str) -> tuple[bool, str]:
    path = Path(raw_path).expanduser()
    if path.exists():
        if not path.is_dir():
            return False, f"Path exists but is not a directory: {path}"
        writable = os.access(path, os.W_OK)
        return writable, (
            f"Directory is {'writable' if writable else 'not writable'}: {path}"
        )

    anchor = path
    while not anchor.exists() and anchor != anchor.parent:
        anchor = anchor.parent
    if not anchor.exists():
        return False, f"No existing parent directory found for: {path}"

    writable = os.access(anchor, os.W_OK)
    return writable, (
        f"Directory does not exist yet but parent is writable: {anchor}"
        if writable
        else f"Directory does not exist and parent is not writable: {anchor}"
    )


def _can_resolve_host(host: str) -> bool:
    try:
        socket.getaddrinfo(host, 443)
        return True
    except Exception:
        return False


def _read_yaml_dict(path: str) -> dict[str, Any]:
    payload_path = Path(path)
    if not payload_path.exists():
        return {}
    try:
        data = yaml.safe_load(payload_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _write_json_atomic(path: str, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    tmp.replace(p)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
