from __future__ import annotations

from digest.models import Item
from digest.pipeline.clean_text import clean_youtube_text


def normalize_items(items: list[Item]) -> list[Item]:
    normalized: list[Item] = []
    for item in items:
        item.title = " ".join(item.title.split())
        if item.type == "video":
            cleaned = clean_youtube_text(item.raw_text)
            item.raw_text = " ".join(cleaned.split())
            item.description = " ".join(clean_youtube_text(item.description).split())
        else:
            item.raw_text = " ".join(item.raw_text.split())
        normalized.append(item)
    return normalized
