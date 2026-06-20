"""CORS, API-auth, and secret-redaction helpers for the web control plane.

These are pure functions and configuration constants extracted from
``digest.web.app``. They read environment configuration and operate on plain
values; they hold no route or application state.
"""

from __future__ import annotations

import hmac
import os
import re
from typing import Any

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
