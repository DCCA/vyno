"""Source health, preview, identity, and error-parsing helpers for the web
control plane.

These functions are extracted from ``digest.web.app``; they build the source
health and preview payloads consumed by the operator console and hold no route
state. ``WebSettings`` is referenced only as a type annotation, so it is guarded
behind ``TYPE_CHECKING`` to avoid a circular import with ``digest.web.app``.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from digest.ops.profile_registry import (
    load_effective_profile_dict,
    save_profile_overlay,
)
from digest.ops.source_registry import visible_source_entries
from digest.storage.sqlite_store import SQLiteStore
from digest.web.link_preview import fetch_link_preview_metadata

if TYPE_CHECKING:
    from digest.web.app import WebSettings


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
