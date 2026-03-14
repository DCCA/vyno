from __future__ import annotations

import urllib.parse

from digest.constants import (
    DIGEST_MUST_READ_LIMIT,
    DIGEST_SKIM_LIMIT,
    DIGEST_TOTAL_LIMIT,
    DIGEST_VIDEO_LIMIT,
)
from digest.models import DigestSections, ScoredItem


def rank_scored_items(
    scored_items: list[ScoredItem],
    *,
    rank_overrides: dict[str, float] | None = None,
) -> list[ScoredItem]:
    overrides = rank_overrides or {}
    return sorted(
        scored_items,
        key=lambda si: float(overrides.get(si.item.id, si.score.total)),
        reverse=True,
    )


def select_digest_sections(
    scored_items: list[ScoredItem],
    *,
    rank_overrides: dict[str, float] | None = None,
    must_read_max_per_source: int = 2,
    digest_max_per_source: int = 3,
) -> DigestSections:
    ranked = rank_scored_items(scored_items, rank_overrides=rank_overrides)
    videos = [i for i in ranked if i.item.type == "video"][:DIGEST_VIDEO_LIMIT]
    non_videos = [i for i in ranked if i.item.type != "video"]
    must_read = _select_must_read(non_videos, max_per_source=must_read_max_per_source)
    must_read_ids = {item.item.id for item in must_read}
    skim = _select_skim(
        [i for i in non_videos if i.item.id not in must_read_ids],
        selected=must_read,
        max_per_source=digest_max_per_source,
    )

    total = must_read + skim + videos
    total = total[:DIGEST_TOTAL_LIMIT]

    must_read = [i for i in total if i in must_read][:DIGEST_MUST_READ_LIMIT]
    skim = [i for i in total if i in skim][:DIGEST_SKIM_LIMIT]
    videos = [i for i in total if i in videos][:DIGEST_VIDEO_LIMIT]

    return DigestSections(must_read=must_read, skim=skim, videos=videos)


def source_bucket(raw: str) -> str:
    value = (raw or "").strip().lower()
    if not value:
        return "unknown"
    if value.startswith("github:"):
        return "github"
    if value.startswith("http://") or value.startswith("https://"):
        parsed = urllib.parse.urlparse(value)
        host = (parsed.netloc or "").strip().lower()
        if host.startswith("www."):
            host = host[4:]
        return host or value
    return value


def count_source_buckets(
    scored_items: list[ScoredItem],
    *,
    include_videos: bool = False,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for scored in scored_items:
        if not include_videos and scored.item.type == "video":
            continue
        bucket = source_bucket(scored.item.source)
        counts[bucket] = counts.get(bucket, 0) + 1
    return counts


def respects_source_cap(
    scored_items: list[ScoredItem],
    *,
    max_per_source: int,
    include_videos: bool = False,
) -> bool:
    if max_per_source <= 0:
        return True
    return all(
        count <= max_per_source
        for count in count_source_buckets(
            scored_items,
            include_videos=include_videos,
        ).values()
    )


def select_skim_items(
    candidates: list[ScoredItem],
    *,
    selected: list[ScoredItem],
    max_per_source: int,
) -> list[ScoredItem]:
    return _select_skim(
        candidates,
        selected=selected,
        max_per_source=max_per_source,
    )


def _select_must_read(
    non_videos: list[ScoredItem],
    *,
    max_per_source: int,
) -> list[ScoredItem]:
    if max_per_source <= 0:
        return non_videos[:DIGEST_MUST_READ_LIMIT]

    selected: list[ScoredItem] = []
    selected_ids: set[str] = set()
    source_counts: dict[str, int] = {}

    for scored in non_videos:
        source = source_bucket(scored.item.source)
        if source_counts.get(source, 0) >= max_per_source:
            continue
        selected.append(scored)
        selected_ids.add(scored.item.id)
        source_counts[source] = source_counts.get(source, 0) + 1
        if len(selected) >= DIGEST_MUST_READ_LIMIT:
            return selected

    for scored in non_videos:
        if scored.item.id in selected_ids:
            continue
        selected.append(scored)
        if len(selected) >= DIGEST_MUST_READ_LIMIT:
            break

    return selected


def _select_skim(
    candidates: list[ScoredItem],
    *,
    selected: list[ScoredItem],
    max_per_source: int,
) -> list[ScoredItem]:
    if max_per_source <= 0:
        return candidates[:DIGEST_SKIM_LIMIT]

    selected_ids = {row.item.id for row in selected}
    counts: dict[str, int] = {}
    for row in selected:
        source = source_bucket(row.item.source)
        counts[source] = counts.get(source, 0) + 1

    skim: list[ScoredItem] = []
    for scored in candidates:
        if scored.item.id in selected_ids:
            continue
        source = source_bucket(scored.item.source)
        if counts.get(source, 0) >= max_per_source:
            continue
        skim.append(scored)
        counts[source] = counts.get(source, 0) + 1
        if len(skim) >= DIGEST_SKIM_LIMIT:
            return skim

    return skim
