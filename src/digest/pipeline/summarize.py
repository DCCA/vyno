from __future__ import annotations

from digest.models import Item, Summary


class FallbackSummarizer:
    def __init__(self, primary, fallback) -> None:
        self.primary = primary
        self.fallback = fallback

    def summarize(self, item: Item) -> tuple[Summary, str | None]:
        try:
            return self.primary.summarize(item), None
        except Exception as exc:
            summary = self.fallback.summarize(item)
            return summary, str(exc)
