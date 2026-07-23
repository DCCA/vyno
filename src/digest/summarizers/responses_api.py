from __future__ import annotations

from typing import Any

from digest.constants import DEFAULT_OPENAI_MODEL
from digest.llm import structured_model
from digest.models import Item, Summary

_SYSTEM_PROMPT = (
    "Summarize AI content into strict JSON with keys: "
    "tldr, key_points (array), why_it_matters."
)

_SCHEMA = {
    "title": "digest_summary",
    "type": "object",
    "properties": {
        "tldr": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "why_it_matters": {"type": "string"},
    },
    "required": ["tldr", "key_points", "why_it_matters"],
    "additionalProperties": False,
}


class ResponsesAPISummarizer:
    provider = "openai_responses"

    def __init__(
        self,
        model: str = DEFAULT_OPENAI_MODEL,
        timeout: int = 30,
        retries: int = 2,
        retry_backoff_seconds: float = 0.6,
        *,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.timeout = timeout
        # `retries` maps onto the OpenAI client's transient-retry budget, which
        # retries 429/5xx/timeouts but not 4xx — preserving prior behavior.
        self.retries = max(0, int(retries))
        self.retry_backoff_seconds = max(0.0, float(retry_backoff_seconds))
        self._client = client or structured_model(
            model=model,
            schema=_SCHEMA,
            timeout=timeout,
            max_retries=self.retries,
        )

    def summarize(self, item: Item) -> Summary:
        user_text = f"TITLE: {item.title}\nURL: {item.url}\nTEXT: {item.raw_text[:6000]}"
        try:
            parsed = self._client.invoke(
                [("system", _SYSTEM_PROMPT), ("user", user_text)]
            )
        except Exception as exc:  # normalize transport/parse errors
            raise RuntimeError(f"Responses API request failed: {exc}") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("Responses API output missing structured JSON")

        return Summary(
            tldr=str(parsed.get("tldr", "")).strip()[:280],
            key_points=[str(p).strip() for p in parsed.get("key_points", [])][:5],
            why_it_matters=str(parsed.get("why_it_matters", "")).strip()[:280],
            provider=self.provider,
        )
