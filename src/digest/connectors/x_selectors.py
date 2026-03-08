from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone

from digest.config import SourceConfig
from digest.connectors.x_provider import XPostPayload, get_x_provider
from digest.models import Item
from digest.storage.sqlite_store import SQLiteStore

SelectorItemLink = tuple[str, str, Item]


def fetch_x_selector_items_linked(
    sources: SourceConfig,
    store: SQLiteStore,
    *,
    provider_mode: str = "",
    default_limit: int = 25,
) -> tuple[list[SelectorItemLink], list[str]]:
    linked_items: list[SelectorItemLink] = []
    errors: list[str] = []
    limit = _resolve_limit(default_limit)

    if not sources.x_authors and not sources.x_themes:
        return linked_items, errors

    provider = get_x_provider(provider_mode)

    for author in sources.x_authors:
        cursor = store.get_x_cursor("x_author", author)
        try:
            posts, next_cursor = provider.fetch_author_posts(
                author=author,
                cursor=cursor,
                limit=limit,
            )
            linked_items.extend(
                [
                    ("x_author", author, _to_item(post, selector_type="x_author", selector_value=author))
                    for post in posts
                ]
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
        cursor = store.get_x_cursor("x_theme", theme)
        try:
            posts, next_cursor = provider.fetch_theme_posts(
                query=theme,
                cursor=cursor,
                limit=limit,
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
) -> tuple[list[Item], list[str]]:
    linked_items, errors = fetch_x_selector_items_linked(
        sources,
        store,
        provider_mode=provider_mode,
        default_limit=default_limit,
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
