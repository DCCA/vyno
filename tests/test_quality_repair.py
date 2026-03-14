import unittest
from datetime import datetime

from digest.models import DigestSections, Item, Score, ScoredItem
from digest.quality.online_repair import (
    rebuild_sections_with_repair,
    validate_repaired_must_read,
)


def _mk(idx: int, source: str, total: int) -> ScoredItem:
    item = Item(
        id=str(idx),
        url=f"https://e/{idx}",
        title=f"T{idx}",
        source=source,
        author=None,
        published_at=datetime.now(),
        type="article",
        raw_text="x",
    )
    score = Score(str(idx), 20, 10, 5, total)
    return ScoredItem(item=item, score=score)


class TestQualityRepair(unittest.TestCase):
    def test_validate_repaired_must_read_rejects_source_concentration(self):
        must_read = [
            _mk(1, "https://arxiv.org/rss/cs.AI", 100),
            _mk(2, "https://arxiv.org/rss/cs.LG", 99),
            _mk(3, "https://arxiv.org/rss/cs.CL", 98),
            _mk(4, "https://news.ycombinator.com/rss", 97),
            _mk(5, "https://www.theverge.com/rss/tech/index.xml", 96),
        ]
        error = validate_repaired_must_read(
            must_read,
            must_read_max_per_source=2,
            digest_max_per_source=3,
        )
        self.assertEqual(error, "must-read source cap violated")

    def test_rebuild_sections_with_repair_reapplies_digest_cap(self):
        ranked_non_videos = [
            _mk(1, "https://arxiv.org/rss/cs.AI", 100),
            _mk(2, "https://news.ycombinator.com/rss", 99),
            _mk(3, "https://www.theverge.com/rss/tech/index.xml", 98),
            _mk(4, "https://simonwillison.net/atom/everything/", 97),
            _mk(5, "https://blog.google/innovation-and-ai/technology/ai/rss/", 96),
            _mk(6, "https://arxiv.org/rss/cs.LG", 95),
            _mk(7, "https://arxiv.org/rss/cs.CL", 94),
            _mk(8, "https://arxiv.org/rss/cs.IR", 93),
            _mk(9, "https://arxiv.org/rss/cs.CV", 92),
            _mk(10, "https://feeds.arstechnica.com/arstechnica/index", 91),
            _mk(11, "https://www.latent.space/feed", 90),
            _mk(12, "https://www.interconnects.ai/feed", 89),
        ]
        sections = DigestSections(
            must_read=ranked_non_videos[:5],
            skim=[],
            videos=[],
        )

        rebuilt = rebuild_sections_with_repair(
            sections,
            ranked_non_videos,
            ["1", "2", "3", "6", "10"],
            must_read_max_per_source=2,
            digest_max_per_source=3,
        )
        combined = rebuilt.must_read + rebuilt.skim
        arxiv_count = sum(1 for row in combined if "arxiv.org" in row.item.source)
        self.assertLessEqual(arxiv_count, 3)
        self.assertEqual([row.item.id for row in rebuilt.must_read], ["1", "2", "3", "6", "10"])


if __name__ == "__main__":
    unittest.main()
