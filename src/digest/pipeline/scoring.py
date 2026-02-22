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
    return Score(item_id=item.id, relevance=relevance, quality=quality, novelty=novelty, total=total, reason=reason)


def score_items(items: list[Item], profile: ProfileConfig) -> list[Score]:
    return [score_item(item, profile) for item in items if not _is_blocked(item, profile)]


def _is_blocked(item: Item, profile: ProfileConfig) -> bool:
    return any(src.lower() in item.source.lower() for src in profile.blocked_sources)
