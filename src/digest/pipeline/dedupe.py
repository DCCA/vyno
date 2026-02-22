from __future__ import annotations

import re
from collections import defaultdict

from digest.models import Item

TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def dedupe_exact(items: list[Item]) -> list[Item]:
    seen: set[str] = set()
    deduped: list[Item] = []
    for item in items:
        key = item.url or item.hash
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


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
