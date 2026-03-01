from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from digest.constants import DEFAULT_OPENAI_MODEL
from digest.models import Item, Summary


class ResponsesAPISummarizer:
    provider = "openai_responses"

    def __init__(
        self,
        model: str = DEFAULT_OPENAI_MODEL,
        timeout: int = 30,
        retries: int = 2,
        retry_backoff_seconds: float = 0.6,
    ) -> None:
        self.model = model
        self.timeout = timeout
        self.retries = max(0, int(retries))
        self.retry_backoff_seconds = max(0.0, float(retry_backoff_seconds))
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required for Responses API summarization"
            )

    def summarize(self, item: Item) -> Summary:
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Summarize AI content into strict JSON with keys: tldr, key_points (array), why_it_matters.",
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"TITLE: {item.title}\nURL: {item.url}\nTEXT: {item.raw_text[:6000]}",
                        }
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "digest_summary",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "tldr": {"type": "string"},
                            "key_points": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "why_it_matters": {"type": "string"},
                        },
                        "required": ["tldr", "key_points", "why_it_matters"],
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
        raw = self._request_with_retries(req)

        parsed = _extract_json_output(raw)
        return Summary(
            tldr=str(parsed.get("tldr", "")).strip()[:280],
            key_points=[str(p).strip() for p in parsed.get("key_points", [])][:5],
            why_it_matters=str(parsed.get("why_it_matters", "")).strip()[:280],
            provider=self.provider,
        )

    def _request_with_retries(self, req: urllib.request.Request) -> dict:
        attempts = self.retries + 1
        last_err: Exception | None = None
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                last_err = exc
                if not _is_retryable_http(exc.code) or attempt >= attempts - 1:
                    raise RuntimeError(f"Responses API HTTPError: {exc.code}") from exc
            except TimeoutError as exc:
                last_err = exc
                if attempt >= attempts - 1:
                    raise RuntimeError("Responses API timeout") from exc
            except urllib.error.URLError as exc:
                last_err = exc
                if not _is_retryable_url_error(exc) or attempt >= attempts - 1:
                    raise RuntimeError("Responses API connection error") from exc

            if self.retry_backoff_seconds > 0:
                time.sleep(self.retry_backoff_seconds * (attempt + 1))

        if last_err is not None:
            raise RuntimeError("Responses API request failed") from last_err
        raise RuntimeError("Responses API request failed")


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
    # fallback for other response shapes
    text = raw.get("output_text", "{}")
    if isinstance(text, str):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Responses API returned non-JSON output") from exc
    raise RuntimeError("Responses API output missing structured JSON")


def _is_retryable_http(code: int) -> bool:
    return code == 429 or code >= 500


def _is_retryable_url_error(exc: urllib.error.URLError) -> bool:
    reason = str(getattr(exc, "reason", "") or exc).lower()
    retry_markers = (
        "timed out",
        "timeout",
        "temporary failure",
        "connection reset",
        "connection refused",
        "remote end closed",
    )
    return any(marker in reason for marker in retry_markers)
