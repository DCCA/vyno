import unittest
from datetime import datetime

from digest.delivery.obsidian import render_obsidian_note
from digest.delivery.source_buckets import build_source_buckets, classify_source_bucket, top_highlights
from digest.delivery.telegram import render_telegram_messages
from digest.models import DigestSections, Item, Score, ScoredItem, Summary


def _row(idx: int, item_type: str, source: str, total: int) -> ScoredItem:
    item = Item(str(idx), f"https://e/{idx}", f"Title {idx}", source, None, datetime.now(), item_type, "body")
    score = Score(str(idx), 1, 1, 1, total, tags=["llm"])
    summary = Summary(tldr=f"Summary {idx}", key_points=["kp"], why_it_matters="why")
    return ScoredItem(item=item, score=score, summary=summary)


class TestSourceSegmentedRendering(unittest.TestCase):
    def test_classify_source_bucket(self):
        self.assertEqual(classify_source_bucket(_row(1, "github_release", "github:openai/openai-cookbook", 10)), "GitHub")
        self.assertEqual(classify_source_bucket(_row(2, "video", "youtube", 9)), "Video")
        self.assertEqual(classify_source_bucket(_row(3, "x_post", "x.com", 8)), "X / Social")
        self.assertEqual(classify_source_bucket(_row(4, "article", "rss", 7)), "Research & Articles")

    def test_build_source_buckets_respects_limits(self):
        sec = DigestSections(
            must_read=[_row(i, "github_repo", "github:org/repo", 100 - i) for i in range(1, 8)],
            skim=[],
            videos=[],
        )
        buckets = build_source_buckets(sec, per_bucket_limit=3)
        self.assertIn("GitHub", buckets)
        self.assertEqual(len(buckets["GitHub"]), 3)

    def test_top_highlights_sorted_by_score(self):
        sec = DigestSections(
            must_read=[_row(1, "article", "rss", 5), _row(2, "article", "rss", 30)],
            skim=[_row(3, "video", "youtube", 20)],
            videos=[],
        )
        top = top_highlights(sec, limit=2)
        self.assertEqual([x.item.id for x in top], ["2", "3"])

    def test_telegram_source_segmented_mode(self):
        sec = DigestSections(
            must_read=[_row(1, "github_release", "github:org/repo", 30)],
            skim=[_row(2, "article", "rss", 20)],
            videos=[_row(3, "video", "youtube", 10)],
        )
        chunks = render_telegram_messages("2026-02-21", sec, render_mode="source_segmented", max_len=2000)
        self.assertTrue(chunks)
        text = "\n".join(chunks)
        self.assertIn("Top Highlights", text)
        self.assertIn("GitHub", text)
        self.assertIn("Research & Articles", text)
        self.assertIn("Video", text)

    def test_obsidian_source_segmented_mode(self):
        sec = DigestSections(
            must_read=[_row(1, "github_release", "github:org/repo", 30)],
            skim=[_row(2, "article", "rss", 20)],
            videos=[_row(3, "video", "youtube", 10)],
        )
        note = render_obsidian_note(
            "2026-02-21",
            sec,
            source_count=3,
            run_id="abc",
            generated_at_utc="2026-02-21T00:00:00+00:00",
            render_mode="source_segmented",
        )
        self.assertIn("## Top Highlights", note)
        self.assertIn("## GitHub", note)
        self.assertIn("## Research & Articles", note)
        self.assertIn("## Video", note)


if __name__ == "__main__":
    unittest.main()
