from __future__ import annotations

from digest.config import ProfileConfig
from digest.models import Item, Score

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


def _contains_any(text: str, words: list[str] | set[str]) -> int:
    t = text.lower()
    return sum(1 for w in words if w.lower() in t)


def score_item(item: Item, profile: ProfileConfig) -> Score:
    text = f"{item.title} {item.description} {item.raw_text}".lower()

    relevance = min(60, _contains_any(text, AI_KEYWORDS) * 6)
    relevance += min(15, _contains_any(text, profile.topics + profile.entities) * 5)
    relevance = max(0, min(60, relevance - _contains_any(text, profile.exclusions) * 10))

    quality = 10
    if any(src.lower() in item.source.lower() for src in profile.trusted_sources):
        quality += 12
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
    return any(src.lower() in item.source.lower() for src in profile.blocked_sources)


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
    if any(k in text for k in ["release", "launch", "announced"]):
        format_tags.append("release-note")
    if any(k in text for k in ["opinion", "thoughts"]):
        format_tags.append("opinion")
    if not format_tags:
        format_tags.append("news")

    tags = list(dict.fromkeys(topic_tags + format_tags))[:5]
    return tags, topic_tags[:5], format_tags[:5]
