import unittest
from datetime import datetime

from digest.delivery.obsidian import render_obsidian_note
from digest.delivery.telegram import render_telegram_message, render_telegram_messages
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
        self.assertIn("generated_at_utc:", note)
        self.assertIn("source_count:", note)
        self.assertIn("[!summary]", note)
        self.assertIn("Tags: llm, benchmark", note)

    def test_telegram_messages_chunk_under_limit(self):
        long_summary = "x" * 500
        items = []
        for i in range(1, 35):
            item = Item(str(i), f"https://x/{i}", f"Title {i}", "src", None, datetime.now(), "article", "body")
            score = Score(str(i), 1, 1, 1, 3, tags=["llm"])
            summary = Summary(tldr=long_summary, key_points=["kp"], why_it_matters="why")
            items.append(ScoredItem(item=item, score=score, summary=summary))
        sec = DigestSections(must_read=items[:10], skim=items[10:25], videos=items[25:30])
        chunks = render_telegram_messages("2026-02-21", sec, max_len=800)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 800)
        self.assertIn("Must-read", chunks[0])

    def test_telegram_caps_overlong_fields(self):
        long_title = "T" * 400
        long_tldr = "S" * 900
        item = Item("1", "https://x/1", long_title, "src", None, datetime.now(), "article", "body")
        score = Score("1", 1, 1, 1, 3, tags=["llm"])
        summary = Summary(tldr=long_tldr, key_points=["kp"], why_it_matters="why")
        sec = DigestSections(must_read=[ScoredItem(item=item, score=score, summary=summary)], skim=[], videos=[])
        msg = render_telegram_message("2026-02-21", sec)
        self.assertLess(len(msg), 1200)

    def test_obsidian_caps_overlong_fields(self):
        long_title = "A" * 400
        long_tldr = "B" * 900
        long_why = "C" * 900
        item = Item("1", "https://x/1", long_title, "src", None, datetime.now(), "article", "body")
        score = Score("1", 1, 1, 1, 3, tags=["llm"])
        summary = Summary(tldr=long_tldr, key_points=["kp"], why_it_matters=long_why)
        sec = DigestSections(must_read=[ScoredItem(item=item, score=score, summary=summary)], skim=[], videos=[])
        note = render_obsidian_note("2026-02-21", sec, source_count=1, run_id="r1", generated_at_utc="2026-02-21T00:00:00+00:00")
        self.assertLess(len(note), 1800)

    def test_renderer_cleans_sponsor_terms(self):
        item = Item("1", "https://x/1", "Demo", "src", None, datetime.now(), "article", "body")
        score = Score("1", 1, 1, 1, 3, tags=["llm"])
        summary = Summary(
            tldr="Check out our Patreon sponsor for details",
            key_points=["kp"],
            why_it_matters="Sponsor-driven",
        )
        sec = DigestSections(must_read=[ScoredItem(item=item, score=score, summary=summary)], skim=[], videos=[])
        note = render_obsidian_note("2026-02-21", sec, source_count=1, run_id="r1", generated_at_utc="2026-02-21T00:00:00+00:00")
        msg = render_telegram_message("2026-02-21", sec)
        self.assertNotIn("patreon", note.lower())
        self.assertNotIn("sponsor", msg.lower())

    def test_renderer_keeps_single_item_link(self):
        item = Item("1", "https://x/1", "Demo", "src", None, datetime.now(), "article", "body")
        score = Score("1", 1, 1, 1, 3, tags=["llm"])
        summary = Summary(tldr="TLDR", key_points=["kp"], why_it_matters="why")
        sec = DigestSections(must_read=[ScoredItem(item=item, score=score, summary=summary)], skim=[], videos=[])
        note = render_obsidian_note("2026-02-21", sec, source_count=1, run_id="r1", generated_at_utc="2026-02-21T00:00:00+00:00")
        msg = render_telegram_message("2026-02-21", sec)
        self.assertEqual(note.count("https://x/1"), 1)
        self.assertEqual(msg.count("https://x/1"), 1)


if __name__ == "__main__":
    unittest.main()
