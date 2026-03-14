from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

from digest.config import SourceConfig
from digest.connectors.x_provider import XPostPayload, get_x_provider
from digest.models import Item
from digest.storage.sqlite_store import SQLiteStore
from digest.web.link_preview import fetch_link_preview_metadata

SelectorItemLink = tuple[str, str, Item]


def fetch_x_selector_items_linked(
    sources: SourceConfig,
    store: SQLiteStore,
    *,
    provider_mode: str = "",
    default_limit: int = 25,
    author_limits: dict[str, int] | None = None,
    theme_limits: dict[str, int] | None = None,
) -> tuple[list[SelectorItemLink], list[str]]:
    linked_items: list[SelectorItemLink] = []
    errors: list[str] = []
    limit = _resolve_limit(default_limit)
    preview_cache: dict[str, dict[str, str]] = {}

    if not sources.x_authors and not sources.x_themes:
        return linked_items, errors

    provider = get_x_provider(provider_mode)

    for author in sources.x_authors:
        limit_for_author = _selector_limit_for(
            author,
            limits=author_limits,
            fallback=limit,
        )
        if limit_for_author <= 0:
            continue
        cursor = store.get_x_cursor("x_author", author)
        try:
            posts, next_cursor = provider.fetch_author_posts(
                author=author,
                cursor=cursor,
                limit=limit_for_author,
            )
            linked_items.extend(
                [
                    ("x_author", author, _to_item(post, selector_type="x_author", selector_value=author))
                    for post in posts
                ]
            )
            linked_items.extend(
                _promote_author_links(
                    posts,
                    author=author,
                    preview_cache=preview_cache,
                )
            )
            last_item_id = posts[-1].id if posts else None
            if next_cursor or last_item_id:
                store.set_x_cursor(
                    selector_type="x_author",
                    selector_value=author,
                    cursor=next_cursor,
                    last_item_id=last_item_id,
                )
        except Exception as exc:
            errors.append(f"x_author:{author}: {exc}")

    for theme in sources.x_themes:
        limit_for_theme = _selector_limit_for(
            theme,
            limits=theme_limits,
            fallback=limit,
        )
        if limit_for_theme <= 0:
            continue
        cursor = store.get_x_cursor("x_theme", theme)
        try:
            posts, next_cursor = provider.fetch_theme_posts(
                query=theme,
                cursor=cursor,
                limit=limit_for_theme,
            )
            linked_items.extend(
                [
                    ("x_theme", theme, _to_item(post, selector_type="x_theme", selector_value=theme))
                    for post in posts
                ]
            )
            last_item_id = posts[-1].id if posts else None
            if next_cursor or last_item_id:
                store.set_x_cursor(
                    selector_type="x_theme",
                    selector_value=theme,
                    cursor=next_cursor,
                    last_item_id=last_item_id,
                )
        except Exception as exc:
            errors.append(f"x_theme:{theme}: {exc}")

    return linked_items, errors


def fetch_x_selector_items(
    sources: SourceConfig,
    store: SQLiteStore,
    *,
    provider_mode: str = "",
    default_limit: int = 25,
    author_limits: dict[str, int] | None = None,
    theme_limits: dict[str, int] | None = None,
) -> tuple[list[Item], list[str]]:
    linked_items, errors = fetch_x_selector_items_linked(
        sources,
        store,
        provider_mode=provider_mode,
        default_limit=default_limit,
        author_limits=author_limits,
        theme_limits=theme_limits,
    )
    return [item for _selector_type, _selector_value, item in linked_items], errors


def _resolve_limit(default_value: int) -> int:
    raw = str(os.getenv("DIGEST_X_MAX_ITEMS_PER_SELECTOR", "") or "").strip()
    if raw:
        try:
            parsed = int(raw)
        except Exception:
            parsed = default_value
    else:
        parsed = default_value
    return max(5, min(100, int(parsed)))


def _selector_limit_for(
    selector: str,
    *,
    limits: dict[str, int] | None,
    fallback: int,
) -> int:
    if limits is None:
        return _resolve_limit(fallback)
    requested = int(limits.get(selector, 0) or 0)
    if requested <= 0:
        return 0
    raw = str(os.getenv("DIGEST_X_MAX_ITEMS_PER_SELECTOR", "") or "").strip()
    if raw:
        try:
            env_cap = max(1, min(100, int(raw)))
        except Exception:
            env_cap = 100
        requested = min(requested, env_cap)
    return max(0, min(100, requested))


def _resolve_promoted_link_limit(default_value: int = 2) -> int:
    raw = str(os.getenv("DIGEST_X_MAX_LINKS_PER_POST", "") or "").strip()
    if raw:
        try:
            parsed = int(raw)
        except Exception:
            parsed = default_value
    else:
        parsed = default_value
    return max(0, min(5, int(parsed)))


def _to_item(post: XPostPayload, *, selector_type: str, selector_value: str) -> Item:
    canonical_url = str(post.url or "").strip()
    digest = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()
    context = f"selector={selector_type}:{selector_value}"
    outbound = " ".join(post.outbound_urls)
    raw_text = " | ".join(part for part in [post.text, context, outbound] if part).strip()
    published = post.created_at or datetime.now(timezone.utc)
    return Item(
        id=digest[:16],
        url=canonical_url,
        title=f"X post by @{post.author_username}",
        source="x.com",
        author=post.author_username,
        published_at=published,
        type="x_post",
        raw_text=raw_text,
        description=post.text,
        hash=digest,
    )


def _promote_author_links(
    posts: list[XPostPayload],
    *,
    author: str,
    preview_cache: dict[str, dict[str, str]],
) -> list[SelectorItemLink]:
    linked: list[SelectorItemLink] = []
    per_post_limit = _resolve_promoted_link_limit()
    if per_post_limit <= 0:
        return linked

    for post in posts:
        promoted_count = 0
        for outbound in post.outbound_urls:
            candidate = _normalize_outbound_url(outbound)
            if not candidate or not _is_promotable_url(candidate):
                continue
            if candidate not in preview_cache:
                preview_cache[candidate] = _safe_preview(candidate)
            linked.append(
                ("x_author", author, _promoted_link_item(post, author=author, preview=preview_cache[candidate]))
            )
            promoted_count += 1
            if promoted_count >= per_post_limit:
                break
    return linked


def _normalize_outbound_url(url: str) -> str:
    value = str(url or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return value


def _is_promotable_url(url: str) -> bool:
    host = _host_label(url)
    return host not in {"x.com", "twitter.com"}


def _safe_preview(url: str) -> dict[str, str]:
    try:
        return fetch_link_preview_metadata(url)
    except Exception:
        return {
            "url": url,
            "resolved_url": url,
            "host": _host_label(url),
            "title": "",
            "description": "",
            "image_url": "",
            "status": "preview_unavailable",
            "error": "",
        }


def _promoted_link_item(
    post: XPostPayload,
    *,
    author: str,
    preview: dict[str, str],
) -> Item:
    resolved_url = str(preview.get("resolved_url") or preview.get("url") or post.url).strip()
    digest = hashlib.sha256(resolved_url.encode("utf-8")).hexdigest()
    host = str(preview.get("host") or "").strip().lower() or _host_label(resolved_url)
    title = str(preview.get("title") or "").strip() or _fallback_title(post, host)
    description = str(preview.get("description") or "").strip() or str(post.text or "").strip()
    author_key = str(author or "").strip().lstrip("@").lower()
    raw_parts = [
        title,
        description,
        str(post.text or "").strip(),
        f"x_endorsed_by:{author_key}" if author_key else "",
        f"x_discovered_from_post:{post.url}" if post.url else "",
    ]
    raw_text = " | ".join(part for part in raw_parts if part)
    published = post.created_at or datetime.now(timezone.utc)
    return Item(
        id=digest[:16],
        url=resolved_url,
        title=title,
        source=host or resolved_url,
        author=None,
        published_at=published,
        type="link",
        raw_text=raw_text,
        description=description,
        hash=digest,
    )


def _host_label(url: str) -> str:
    host = (urlparse(url).netloc or "").strip().lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _fallback_title(post: XPostPayload, host: str) -> str:
    snippet = " ".join(str(post.text or "").split()).strip()
    if snippet:
        return snippet[:120]
    if host:
        return f"Shared from {host}"
    return "Shared link from X"
