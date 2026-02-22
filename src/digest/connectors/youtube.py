from __future__ import annotations

from urllib.parse import quote_plus

from digest.connectors.rss import fetch_rss_items
from digest.models import Item


def _channel_feed(channel_id: str) -> str:
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def _query_feed(query: str) -> str:
    # YouTube has no official RSS search endpoint; this is a best-effort public feed.
    return f"https://www.youtube.com/feeds/videos.xml?search_query={quote_plus(query)}"


def fetch_youtube_items(channels: list[str], queries: list[str], timeout: int = 15) -> list[Item]:
    feeds = [_channel_feed(ch) for ch in channels] + [_query_feed(q) for q in queries]
    items = fetch_rss_items(feeds, timeout=timeout)
    for item in items:
        item.type = "video"
    return items
