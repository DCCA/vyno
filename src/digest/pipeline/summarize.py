from __future__ import annotations

import re

from digest.models import Item, Summary

URL_RE = re.compile(r"https?://\S+")
SPONSOR_PHRASES = ("check out", "sponsor", "patreon", "support us", "sign up")


class FallbackSummarizer:
    def __init__(self, primary, fallback) -> None:
        self.primary = primary
        self.fallback = fallback

    def summarize(self, item: Item) -> tuple[Summary, str | None]:
        try:
            summary = self.primary.summarize(item)
            if is_low_signal_summary(summary):
                fallback_summary = self.fallback.summarize(item)
                return fallback_summary, "low_signal_summary"
            return summary, None
        except Exception as exc:
            summary = self.fallback.summarize(item)
            return summary, str(exc)


def is_low_signal_summary(summary: Summary) -> bool:
    combined = " ".join(
        [
            summary.tldr or "",
            " ".join(summary.key_points or []),
            summary.why_it_matters or "",
        ]
    ).strip()
    lower = combined.lower()

    if len(summary.tldr or "") >= 600:
        return True
    if len(URL_RE.findall(combined)) >= 3:
        return True
    if lower.count("#") >= 5:
        return True
    if any(p in lower for p in SPONSOR_PHRASES):
        return True
    return False
