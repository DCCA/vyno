from __future__ import annotations

import urllib.parse

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
) -> DigestSections:
    ranked = rank_scored_items(scored_items, rank_overrides=rank_overrides)
    videos = [i for i in ranked if i.item.type == "video"][:5]
    non_videos = [i for i in ranked if i.item.type != "video"]
    must_read = _select_must_read(non_videos, max_per_source=must_read_max_per_source)
    must_read_ids = {item.item.id for item in must_read}
    skim = [i for i in non_videos if i.item.id not in must_read_ids][:10]

    total = must_read + skim + videos
    total = total[:20]

    must_read = [i for i in total if i in must_read][:5]
    skim = [i for i in total if i in skim][:10]
    videos = [i for i in total if i in videos][:5]

    return DigestSections(must_read=must_read, skim=skim, videos=videos)


def _select_must_read(
    non_videos: list[ScoredItem],
    *,
    max_per_source: int,
) -> list[ScoredItem]:
    if max_per_source <= 0:
        return non_videos[:5]

    selected: list[ScoredItem] = []
    selected_ids: set[str] = set()
    source_counts: dict[str, int] = {}

    for scored in non_videos:
        source = _source_bucket(scored.item.source)
        if source_counts.get(source, 0) >= max_per_source:
            continue
        selected.append(scored)
        selected_ids.add(scored.item.id)
        source_counts[source] = source_counts.get(source, 0) + 1
        if len(selected) >= 5:
            return selected

    for scored in non_videos:
        if scored.item.id in selected_ids:
            continue
        selected.append(scored)
        if len(selected) >= 5:
            break

    return selected


def _source_bucket(raw: str) -> str:
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
