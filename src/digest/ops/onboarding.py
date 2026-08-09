from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import socket
from typing import Any

import yaml

from digest.ops.profile_registry import load_effective_profile
from digest.ops.source_registry import load_effective_sources


@dataclass(slots=True)
class OnboardingSettings:
    sources_path: str
    sources_overlay_path: str
    profile_path: str
    profile_overlay_path: str
    db_path: str
    run_lock_path: str = ".runtime/run.lock"


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


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
