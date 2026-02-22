import unittest
from datetime import datetime

from digest.models import Item, Score, ScoredItem
from digest.pipeline.selection import select_digest_sections


def _mk(idx: int, t: str = "article") -> ScoredItem:
    item = Item(str(idx), f"https://e/{idx}", f"T{idx}", "src", None, datetime.now(), t, "x")
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


if __name__ == "__main__":
    unittest.main()
