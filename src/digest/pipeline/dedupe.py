from __future__ import annotations

import re

from digest.models import Item

TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def dedupe_exact(items: list[Item]) -> list[Item]:
    merged: dict[str, Item] = {}
    order: list[str] = []
    for item in items:
        key = item.url or item.hash
        if key in merged:
            merged[key] = _merge_duplicate_item(merged[key], item)
            continue
        merged[key] = item
        order.append(key)
    return [merged[key] for key in order]


def _merge_duplicate_item(existing: Item, incoming: Item) -> Item:
    preferred, other = _preferred_item(existing, incoming)
    return Item(
        id=preferred.id,
        url=preferred.url or other.url,
        title=_choose_title(preferred.title, other.title),
        source=_choose_source(preferred.source, other.source),
        author=preferred.author or other.author,
        published_at=preferred.published_at or other.published_at,
        type=_choose_type(preferred.type, other.type),
        raw_text=_merge_text(existing.raw_text, incoming.raw_text),
        description=_choose_description(preferred.description, other.description),
        hash=preferred.hash or other.hash,
    )


def _preferred_item(existing: Item, incoming: Item) -> tuple[Item, Item]:
    return (
        (existing, incoming)
        if _type_priority(existing.type) >= _type_priority(incoming.type)
        else (incoming, existing)
    )


def _type_priority(kind: str) -> int:
    priorities = {
        "article": 40,
        "link": 30,
        "github_release": 25,
        "github_repo": 20,
        "github_issue": 20,
        "github_pr": 20,
        "video": 10,
        "x_post": 5,
    }
    return priorities.get(kind, 0)


def _merge_text(left: str, right: str) -> str:
    parts: list[str] = []
    seen: set[str] = set()
    for value in (left, right):
        clean = " ".join((value or "").split()).strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        parts.append(clean)
    return " | ".join(parts)


def _choose_title(primary: str, secondary: str) -> str:
    one = (primary or "").strip()
    two = (secondary or "").strip()
    if not one:
        return two
    if not two:
        return one
    if one.startswith("X post by @") and not two.startswith("X post by @"):
        return two
    if two.startswith("X post by @") and not one.startswith("X post by @"):
        return one
    return one if len(one) >= len(two) else two


def _choose_source(primary: str, secondary: str) -> str:
    one = (primary or "").strip()
    two = (secondary or "").strip()
    if one in {"x.com", "twitter.com"} and two not in {"", "x.com", "twitter.com"}:
        return two
    return one or two


def _choose_type(primary: str, secondary: str) -> str:
    return primary if _type_priority(primary) >= _type_priority(secondary) else secondary


def _choose_description(primary: str, secondary: str) -> str:
    one = (primary or "").strip()
    two = (secondary or "").strip()
    return one if len(one) >= len(two) else two


def cluster_near_duplicates(items: list[Item], threshold: float = 0.7) -> list[list[Item]]:
    clusters: list[list[Item]] = []
    for item in items:
        candidate = _tokens(item.title)
        placed = False
        for cluster in clusters:
            centroid = _tokens(cluster[0].title)
            if not candidate or not centroid:
                continue
            jaccard = len(candidate & centroid) / len(candidate | centroid)
            if jaccard >= threshold:
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])
    return clusters


def select_cluster_representatives(clusters: list[list[Item]]) -> list[Item]:
    representatives: list[Item] = []
    for cluster in clusters:
        representatives.append(max(cluster, key=lambda item: len(item.raw_text)))
    return representatives


def dedupe_and_cluster(items: list[Item], threshold: float = 0.7) -> list[Item]:
    deduped = dedupe_exact(items)
    clusters = cluster_near_duplicates(deduped, threshold=threshold)
    return select_cluster_representatives(clusters)
