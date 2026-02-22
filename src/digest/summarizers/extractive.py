from __future__ import annotations

import re

from digest.models import Item, Summary

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


class ExtractiveSummarizer:
    provider = "extractive"

    def summarize(self, item: Item) -> Summary:
        text = (item.raw_text or item.description or item.title).strip()
        if not text:
            text = item.title
        sentences = [s.strip() for s in SENTENCE_RE.split(text) if s.strip()]
        tldr = sentences[0] if sentences else item.title
        key_points = sentences[:3] if sentences else [item.title]
        why = f"Useful for tracking AI trend related to: {item.title[:80]}"
        return Summary(tldr=tldr[:280], key_points=key_points, why_it_matters=why[:280], provider=self.provider)
