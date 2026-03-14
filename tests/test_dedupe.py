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

    def test_dedupe_merges_x_discovery_context_into_article(self):
        article = Item(
            "1",
            "https://example.com/article",
            "Article title",
            "https://feed.example.com/rss.xml",
            None,
            datetime.now(),
            "article",
            "article body",
            "article description",
        )
        discovered = Item(
            "2",
            "https://example.com/article",
            "X post by @openai",
            "example.com",
            None,
            datetime.now(),
            "link",
            "shared link | x_endorsed_by:openai",
            "shared from x",
        )
        out = dedupe_exact([article, discovered])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].type, "article")
        self.assertIn("x_endorsed_by:openai", out[0].raw_text)
        self.assertEqual(out[0].title, "Article title")


if __name__ == "__main__":
    unittest.main()
