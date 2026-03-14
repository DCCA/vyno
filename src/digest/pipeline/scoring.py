from __future__ import annotations

import re

from digest.config import ProfileConfig
from digest.models import Item, Score, ScoredItem
from digest.pipeline.selection import source_bucket

AI_KEYWORDS = {
    "llm",
    "agents",
    "eval",
    "rag",
    "tooling",
    "inference",
    "openai",
    "anthropic",
    "model",
    "benchmark",
    "safety",
    "research",
}
CLICKBAIT = {"insane", "shocking", "secret", "10x", "unbelievable"}
TECHNICAL_KEYWORDS = {
    "arxiv",
    "benchmark",
    "kernel",
    "latency",
    "kv cache",
    "throughput",
    "cuda",
    "inference engine",
    "memory bandwidth",
    "quantization",
    "distillation",
    "training dynamics",
    "optimization",
    "gradient",
    "retrieval benchmark",
}
X_ENDORSEMENT_RE = re.compile(r"x_endorsed_by:([a-z0-9_]+)")


def _contains_any(text: str, words: list[str] | set[str]) -> int:
    t = text.lower()
    return sum(1 for w in words if w.lower() in t)


def _count_x_endorsements(text: str) -> int:
    return len({match.group(1) for match in X_ENDORSEMENT_RE.finditer(text.lower())})


def score_item(item: Item, profile: ProfileConfig) -> Score:
    text = f"{item.title} {item.description} {item.raw_text}".lower()

    relevance = min(60, _contains_any(text, AI_KEYWORDS) * 6)
    relevance += min(15, _contains_any(text, profile.topics + profile.entities) * 5)
    relevance = max(0, min(60, relevance - _contains_any(text, profile.exclusions) * 10))

    quality = 10
    if any(src.lower() in item.source.lower() for src in profile.trusted_sources):
        quality += 12
    if item.source == "x.com" and item.author and item.author.lower() in {a.lower() for a in profile.trusted_authors_x}:
        quality += 8
    github_owner = _github_owner(item.source)
    if github_owner and github_owner.lower() in {o.lower() for o in profile.trusted_orgs_github}:
        quality += 8
    quality += min(12, _count_x_endorsements(text) * 4)
    if len(item.raw_text) > 500:
        quality += 8
    quality -= _contains_any(text, CLICKBAIT) * 5
    quality = max(0, min(30, quality))

    novelty = 10
    if "recap" in text or "roundup" in text:
        novelty -= 4
    novelty = max(0, min(10, novelty))

    total = relevance + quality + novelty
    reason = f"rel={relevance};qual={quality};nov={novelty}"
    tags, topic_tags, format_tags = _rule_tags(item)
    return Score(
        item_id=item.id,
        relevance=relevance,
        quality=quality,
        novelty=novelty,
        total=total,
        reason=reason,
        tags=tags,
        topic_tags=topic_tags,
        format_tags=format_tags,
        provider="rules",
    )


def score_items(items: list[Item], profile: ProfileConfig) -> list[Score]:
    return [score_item(item, profile) for item in items if not is_blocked(item, profile)]


def is_blocked(item: Item, profile: ProfileConfig) -> bool:
    if any(src.lower() in item.source.lower() for src in profile.blocked_sources):
        return True
    if item.source == "x.com" and item.author and item.author.lower() in {a.lower() for a in profile.blocked_authors_x}:
        return True
    github_owner = _github_owner(item.source)
    if github_owner and github_owner.lower() in {o.lower() for o in profile.blocked_orgs_github}:
        return True
    return False


def content_depth_adjustment(item: Item, profile: ProfileConfig) -> int:
    preference = str(getattr(profile, "content_depth_preference", "balanced") or "").strip().lower()
    if preference not in {"practical", "balanced", "deep_technical"}:
        preference = "balanced"
    technicality = technicality_level(item)
    if technicality == "high":
        if preference == "practical":
            return -8
        if preference == "balanced":
            return -3
        return 4
    if technicality == "medium":
        if preference == "practical":
            return -4
        if preference == "deep_technical":
            return 2
    return 0


def research_concentration_adjustments(
    scored_items: list[ScoredItem],
    *,
    rank_overrides: dict[str, float] | None = None,
    pool_size: int = 15,
) -> dict[str, float]:
    if pool_size <= 0:
        return {}

    ranked_non_videos = sorted(
        [row for row in scored_items if row.item.type != "video"],
        key=lambda row: float((rank_overrides or {}).get(row.item.id, row.score.total)),
        reverse=True,
    )[:pool_size]
    if not ranked_non_videos:
        return {}

    family_rows: dict[str, list] = {}
    for scored in ranked_non_videos:
        if not _is_research_heavy(scored):
            continue
        bucket = source_bucket(scored.item.source)
        family_rows.setdefault(bucket, []).append(scored)

    adjustments: dict[str, float] = {}
    for rows in family_rows.values():
        if len(rows) <= 3:
            continue
        for index, scored in enumerate(rows, start=1):
            if index <= 2:
                continue
            adjustments[scored.item.id] = adjustments.get(scored.item.id, 0.0) - float(
                min(3, index - 2)
            )
    return adjustments


def technicality_level(item: Item) -> str:
    text = f"{item.title} {item.description} {item.raw_text}".lower()
    signals = 0
    if item.source.startswith("https://arxiv.org") or item.source.startswith("http://arxiv.org"):
        signals += 3
    if item.type in {"github_issue", "github_pr", "github_repo"}:
        signals += 1
    signals += _contains_any(text, TECHNICAL_KEYWORDS)
    if any(token in text for token in {"paper", "ablation", "sota", "state of the art"}):
        signals += 1
    if signals >= 4:
        return "high"
    if signals >= 2:
        return "medium"
    return "low"


def _is_research_heavy(scored: ScoredItem) -> bool:
    if source_bucket(scored.item.source) == "arxiv.org":
        return True
    format_tags = {tag.strip().lower() for tag in scored.score.format_tags}
    if "paper" in format_tags and technicality_level(scored.item) != "low":
        return True
    return False


def _github_owner(source: str) -> str:
    # source format: github:<owner>/<repo> or github:search
    if not source.startswith("github:"):
        return ""
    tail = source.split(":", 1)[1]
    if "/" in tail:
        return tail.split("/", 1)[0]
    return ""


def _rule_tags(item: Item) -> tuple[list[str], list[str], list[str]]:
    text = f"{item.title} {item.description} {item.raw_text}".lower()
    topic_tags: list[str] = []
    format_tags: list[str] = []

    topic_map = {
        "llm": ["llm", "model", "gpt", "claude"],
        "agents": ["agent", "agents", "tool use"],
        "rag": ["rag", "retrieval"],
        "evals": ["eval", "benchmark"],
        "safety": ["safety", "alignment"],
        "research": ["paper", "arxiv", "research"],
        "infra": ["inference", "gpu", "cuda", "latency"],
        "product": ["release", "launch", "feature"],
        "policy": ["policy", "regulation", "government"],
        "open-source": ["open source", "github", "oss"],
    }
    for tag, kws in topic_map.items():
        if any(k in text for k in kws):
            topic_tags.append(tag)

    if item.type == "video":
        format_tags.append("video")
    if any(k in text for k in ["tutorial", "how to", "guide"]):
        format_tags.append("tutorial")
    if any(k in text for k in ["benchmark", "eval"]):
        format_tags.append("benchmark")
    if any(k in text for k in ["paper", "arxiv"]):
        format_tags.append("paper")
    if technicality_level(item) != "low":
        format_tags.append("technical")
    if "x_endorsed_by:" in text:
        format_tags.append("x-discovered")
    if any(k in text for k in ["release", "launch", "announced"]):
        format_tags.append("release-note")
    if any(k in text for k in ["opinion", "thoughts"]):
        format_tags.append("opinion")
    if not format_tags:
        format_tags.append("news")

    tags = list(dict.fromkeys(topic_tags + format_tags))[:5]
    return tags, topic_tags[:5], format_tags[:5]
