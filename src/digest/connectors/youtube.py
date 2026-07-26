from __future__ import annotations

from digest.connectors.rss import fetch_rss_items
from digest.models import Item


def _channel_feed(channel_id: str) -> str:
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def fetch_youtube_items(channels: list[str], timeout: int = 15) -> list[Item]:
    items = fetch_rss_items([_channel_feed(ch) for ch in channels], timeout=timeout)
    for item in items:
        item.type = "video"
    return items
