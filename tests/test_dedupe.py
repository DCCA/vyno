import unittest
from datetime import datetime

from digest.models import Item
from digest.pipeline.dedupe import dedupe_exact


class TestDedupe(unittest.TestCase):
    def test_dedupe_exact_by_url(self):
        one = Item("1", "https://x", "A", "s", None, datetime.now(), "article", "body")
        two = Item("2", "https://x", "B", "s", None, datetime.now(), "article", "body")
        out = dedupe_exact([one, two])
        self.assertEqual(len(out), 1)


if __name__ == "__main__":
    unittest.main()
