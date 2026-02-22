from __future__ import annotations

from collections import OrderedDict

from digest.models import DigestSections, ScoredItem


BUCKET_ORDER = [
    "GitHub",
    "Research & Articles",
    "Video",
    "X / Social",
    "Other",
]


def build_source_buckets(sections: DigestSections, *, per_bucket_limit: int = 10) -> dict[str, list[ScoredItem]]:
    selected = sections.must_read + sections.skim + sections.videos
    ranked = sorted(selected, key=lambda si: si.score.total, reverse=True)

    buckets: dict[str, list[ScoredItem]] = {k: [] for k in BUCKET_ORDER}
    for item in ranked:
        bucket = classify_source_bucket(item)
        rows = buckets[bucket]
        if len(rows) < max(1, per_bucket_limit):
            rows.append(item)

    ordered: "OrderedDict[str, list[ScoredItem]]" = OrderedDict()
    for key in BUCKET_ORDER:
        vals = buckets[key]
        if vals:
            ordered[key] = vals
    return dict(ordered)


def top_highlights(sections: DigestSections, *, limit: int = 3) -> list[ScoredItem]:
    selected = sections.must_read + sections.skim + sections.videos
    ranked = sorted(selected, key=lambda si: si.score.total, reverse=True)
    return ranked[: max(1, limit)]


def classify_source_bucket(scored: ScoredItem) -> str:
    item = scored.item
    source = (item.source or "").lower()
    if item.type.startswith("github_") or source.startswith("github:"):
        return "GitHub"
    if item.type == "video":
        return "Video"
    if item.type == "x_post" or source == "x.com":
        return "X / Social"
    if item.type in {"article", "link"}:
        return "Research & Articles"
    return "Other"
