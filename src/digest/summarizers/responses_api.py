from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from digest.models import Item, Summary


class ResponsesAPISummarizer:
    provider = "openai_responses"

    def __init__(self, model: str = "gpt-4o-mini", timeout: int = 30) -> None:
        self.model = model
        self.timeout = timeout
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required for Responses API summarization")

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
                            "key_points": {"type": "array", "items": {"type": "string"}},
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
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Responses API HTTPError: {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError("Responses API connection error") from exc

        parsed = _extract_json_output(raw)
        return Summary(
            tldr=str(parsed.get("tldr", "")).strip()[:280],
            key_points=[str(p).strip() for p in parsed.get("key_points", [])][:5],
            why_it_matters=str(parsed.get("why_it_matters", "")).strip()[:280],
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
    # fallback for other response shapes
    text = raw.get("output_text", "{}")
    if isinstance(text, str):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Responses API returned non-JSON output") from exc
    raise RuntimeError("Responses API output missing structured JSON")
