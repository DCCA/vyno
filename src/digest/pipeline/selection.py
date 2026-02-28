from __future__ import annotations

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
) -> DigestSections:
    ranked = rank_scored_items(scored_items, rank_overrides=rank_overrides)
    videos = [i for i in ranked if i.item.type == "video"][:5]
    non_videos = [i for i in ranked if i.item.type != "video"]
    must_read = non_videos[:5]
    skim = non_videos[5:15]

    total = must_read + skim + videos
    total = total[:20]

    must_read = [i for i in total if i in must_read][:5]
    skim = [i for i in total if i in skim][:10]
    videos = [i for i in total if i in videos][:5]

    return DigestSections(must_read=must_read, skim=skim, videos=videos)
