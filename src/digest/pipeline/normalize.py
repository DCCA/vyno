from __future__ import annotations

from digest.models import Item


def normalize_items(items: list[Item]) -> list[Item]:
    normalized: list[Item] = []
    for item in items:
        item.title = " ".join(item.title.split())
        item.raw_text = " ".join(item.raw_text.split())
        normalized.append(item)
    return normalized
