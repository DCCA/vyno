from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

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


class ResponsesAPIScorerTagger:
    provider = "agent"

    def __init__(self, model: str = "gpt-5.1-codex-mini", timeout: int = 30) -> None:
        self.model = model
        self.timeout = timeout
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for agent scoring")

    def score_and_tag(self, item: Item) -> Score:
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Score and tag AI content. Return strict JSON with fields: "
                                "relevance(0-10), quality(0-10), novelty(0-10), total(0-30), "
                                "topic_tags(array from allowed list), format_tags(array from allowed list), "
                                "tags(array max 5), reason(short)."
                            ),
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"ALLOWED_TOPIC_TAGS: {', '.join(TOPIC_VOCAB)}\n"
                                f"ALLOWED_FORMAT_TAGS: {', '.join(FORMAT_VOCAB)}\n"
                                f"TITLE: {item.title}\nURL: {item.url}\nSOURCE: {item.source}\n"
                                f"TYPE: {item.type}\nTEXT: {item.raw_text[:8000]}"
                            ),
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "agent_scoring",
                    "schema": {
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
                    },
                }
            },
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Agent scoring HTTPError: {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError("Agent scoring connection error") from exc

        parsed = _extract_json_output(raw)
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
        tags = _normalize_free_tags(parsed.get("tags", []), fallback=topic_tags + format_tags)
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


def _extract_json_output(raw: dict) -> dict:
    output = raw.get("output", [])
    for out in output:
        for content in out.get("content", []):
            if content.get("type") == "output_text":
                text = content.get("text", "{}")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    continue
    text = raw.get("output_text", "{}")
    if isinstance(text, str):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Agent scoring returned non-JSON output") from exc
    raise RuntimeError("Agent scoring output missing structured JSON")


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
