from __future__ import annotations

from digest.models import DigestSections, ScoredItem


def select_digest_sections(scored_items: list[ScoredItem]) -> DigestSections:
    ranked = sorted(scored_items, key=lambda si: si.score.total, reverse=True)
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
