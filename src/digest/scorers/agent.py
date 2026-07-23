from __future__ import annotations

from typing import Any

from digest.constants import DEFAULT_OPENAI_MODEL
from digest.llm import structured_model
from digest.models import Item, Score

TOPIC_VOCAB = [
    "llm",
    "agents",
    "rag",
    "evals",
    "safety",
    "infra",
    "research",
    "product",
    "policy",
    "open-source",
]
FORMAT_VOCAB = [
    "tutorial",
    "benchmark",
    "release-note",
    "opinion",
    "news",
    "paper",
    "video",
    "demo",
]

_SYSTEM_PROMPT = (
    "Score and tag AI content. Return strict JSON with fields: "
    "relevance(0-10), quality(0-10), novelty(0-10), total(0-30), "
    "topic_tags(array from allowed list), format_tags(array from allowed list), "
    "tags(array max 5), reason(short)."
)

_SCHEMA = {
    "title": "agent_scoring",
    "type": "object",
    "properties": {
        "relevance": {"type": "number"},
        "quality": {"type": "number"},
        "novelty": {"type": "number"},
        "total": {"type": "number"},
        "topic_tags": {"type": "array", "items": {"type": "string"}},
        "format_tags": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"},
    },
    "required": [
        "relevance",
        "quality",
        "novelty",
        "total",
        "topic_tags",
        "format_tags",
        "tags",
        "reason",
    ],
    "additionalProperties": False,
}


class ResponsesAPIScorerTagger:
    provider = "agent"

    def __init__(
        self,
        model: str = DEFAULT_OPENAI_MODEL,
        timeout: int = 30,
        *,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.timeout = timeout
        # Building the structured model raises RuntimeError when OPENAI_API_KEY
        # (or langchain-openai) is unavailable, so the caller falls back to the
        # rules scorer just as it did on the old missing-key guard.
        self._client = client or structured_model(
            model=model, schema=_SCHEMA, timeout=timeout
        )

    def score_and_tag(self, item: Item, *, max_text_chars: int = 8000) -> Score:
        text_limit = max(400, int(max_text_chars))
        user_text = (
            f"ALLOWED_TOPIC_TAGS: {', '.join(TOPIC_VOCAB)}\n"
            f"ALLOWED_FORMAT_TAGS: {', '.join(FORMAT_VOCAB)}\n"
            f"TITLE: {item.title}\nURL: {item.url}\nSOURCE: {item.source}\n"
            f"TYPE: {item.type}\nTEXT: {item.raw_text[:text_limit]}"
        )
        try:
            parsed = self._client.invoke(
                [("system", _SYSTEM_PROMPT), ("user", user_text)]
            )
        except Exception as exc:  # normalize transport/parse errors
            raise RuntimeError(f"Agent scoring failed: {exc}") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("Agent scoring returned no structured output")
        _validate_agent_payload(parsed)

        rel10 = _clamp_num(parsed.get("relevance", 0), 0, 10)
        qual10 = _clamp_num(parsed.get("quality", 0), 0, 10)
        nov10 = _clamp_num(parsed.get("novelty", 0), 0, 10)

        # Preserve existing weighting scales for compatibility with selection behavior.
        relevance = rel10 * 6
        quality = qual10 * 3
        novelty = nov10
        total = relevance + quality + novelty

        topic_tags = _normalize_vocab_tags(parsed.get("topic_tags", []), TOPIC_VOCAB)
        format_tags = _normalize_vocab_tags(parsed.get("format_tags", []), FORMAT_VOCAB)
        tags = _normalize_free_tags(
            parsed.get("tags", []), fallback=topic_tags + format_tags
        )
        reason = str(parsed.get("reason", "")).strip()[:280]

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
            provider=self.provider,
        )


def _validate_agent_payload(payload: dict) -> None:
    required = {
        "relevance": (int, float),
        "quality": (int, float),
        "novelty": (int, float),
        "topic_tags": list,
        "format_tags": list,
        "tags": list,
        "reason": str,
    }
    for key, expected in required.items():
        if key not in payload:
            raise RuntimeError(f"Agent scoring invalid schema: missing {key}")
        if not isinstance(payload[key], expected):
            raise RuntimeError(f"Agent scoring invalid schema: bad {key}")


def _clamp_num(value: object, lo: int, hi: int) -> int:
    try:
        n = int(round(float(value)))
    except Exception:
        n = lo
    return max(lo, min(hi, n))


def _normalize_vocab_tags(values: object, vocab: list[str]) -> list[str]:
    if not isinstance(values, list):
        return []
    allowed = {v.lower(): v for v in vocab}
    out: list[str] = []
    for raw in values:
        if not isinstance(raw, str):
            continue
        k = raw.strip().lower()
        if k in allowed and allowed[k] not in out:
            out.append(allowed[k])
    return out[:5]


def _normalize_free_tags(values: object, fallback: list[str]) -> list[str]:
    out: list[str] = []
    if isinstance(values, list):
        for raw in values:
            if not isinstance(raw, str):
                continue
            tag = raw.strip().lower().replace(" ", "-")
            if tag and tag not in out:
                out.append(tag)
    if not out:
        out = list(dict.fromkeys(fallback))
    return out[:5]
