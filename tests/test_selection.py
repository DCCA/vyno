import unittest
from datetime import datetime

from digest.models import Item, ItemType, Score, ScoredItem
from digest.pipeline.selection import rank_scored_items, select_digest_sections


def _mk(idx: int, t: ItemType = "article", source: str = "src") -> ScoredItem:
    item = Item(
        str(idx), f"https://e/{idx}", f"T{idx}", source, None, datetime.now(), t, "x"
    )
    score = Score(str(idx), 20, 10, 5, 35)
    return ScoredItem(item=item, score=score)


class TestSelection(unittest.TestCase):
    def test_selection_limits(self):
        rows = [_mk(i, "video" if i % 4 == 0 else "article") for i in range(1, 40)]
        sections = select_digest_sections(rows)
        total = len(sections.must_read) + len(sections.skim) + len(sections.videos)
        self.assertLessEqual(total, 20)
        self.assertLessEqual(len(sections.must_read), 5)
        self.assertLessEqual(len(sections.skim), 10)
        self.assertLessEqual(len(sections.videos), 5)

    def test_rank_overrides_can_promote_item(self):
        rows = [_mk(1, "article"), _mk(2, "article"), _mk(3, "article")]
        rows[0].score.total = 90
        rows[1].score.total = 80
        rows[2].score.total = 70
        ranked = rank_scored_items(rows, rank_overrides={"3": 120.0})
        self.assertEqual(ranked[0].item.id, "3")

    def test_selection_uses_rank_overrides(self):
        rows = [_mk(i, "article") for i in range(1, 8)]
        for idx, row in enumerate(rows, start=1):
            row.score.total = 100 - idx
        sections = select_digest_sections(rows, rank_overrides={"7": 200.0})
        self.assertTrue(sections.must_read)
        self.assertEqual(sections.must_read[0].item.id, "7")

    def test_must_read_source_diversity_cap(self):
        rows = []
        for i in range(1, 9):
            rows.append(_mk(i, "article", source="https://arxiv.org/rss/cs.AI"))
            rows[-1].score.total = 100 - i
        rows.append(_mk(90, "article", source="https://news.ycombinator.com/rss"))
        rows[-1].score.total = 60
        rows.append(
            _mk(91, "article", source="https://feeds.arstechnica.com/arstechnica/index")
        )
        rows[-1].score.total = 59
        rows.append(
            _mk(92, "article", source="https://www.theverge.com/rss/tech/index.xml")
        )
        rows[-1].score.total = 58

        sections = select_digest_sections(rows, must_read_max_per_source=2)
        must_sources = [si.item.source for si in sections.must_read]
        self.assertEqual(len(sections.must_read), 5)
        self.assertLessEqual(must_sources.count("https://arxiv.org/rss/cs.AI"), 2)
        self.assertIn("https://news.ycombinator.com/rss", must_sources)


if __name__ == "__main__":
    unittest.main()
