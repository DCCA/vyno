import unittest
from datetime import datetime

from digest.delivery.obsidian import render_obsidian_note
from digest.delivery.telegram import render_telegram_message
from digest.models import DigestSections, Item, Score, ScoredItem, Summary


def _scored(idx: int, kind: str = "article") -> ScoredItem:
    item = Item(str(idx), f"https://x/{idx}", f"Title {idx}", "src", None, datetime.now(), kind, "body")
    score = Score(str(idx), 1, 1, 1, 3, tags=["llm", "benchmark"])
    summary = Summary(tldr="TLDR", key_points=["kp"], why_it_matters="why")
    return ScoredItem(item=item, score=score, summary=summary)


class TestRenderers(unittest.TestCase):
    def test_telegram_and_obsidian_formats(self):
        sec = DigestSections(must_read=[_scored(1)], skim=[_scored(2)], videos=[_scored(3, "video")])
        msg = render_telegram_message("2026-02-21", sec)
        note = render_obsidian_note(
            "2026-02-21",
            sec,
            source_count=3,
            run_id="abc123",
            generated_at_utc="2026-02-21T10:00:00+00:00",
        )
        self.assertIn("Must-read", msg)
        self.assertIn("## Must-read", note)
        self.assertIn("run_id: abc123", note)
        self.assertIn("Tags: llm, benchmark", note)


if __name__ == "__main__":
    unittest.main()
