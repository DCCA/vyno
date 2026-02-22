import unittest
from datetime import datetime

from digest.models import Item
from digest.pipeline.summarize import FallbackSummarizer
from digest.summarizers.extractive import ExtractiveSummarizer


class Broken:
    def summarize(self, item):
        raise RuntimeError("boom")


class TestSummarizerFallback(unittest.TestCase):
    def test_fallback_used_on_error(self):
        item = Item("1", "u", "title", "src", None, datetime.now(), "article", "text")
        fb = FallbackSummarizer(primary=Broken(), fallback=ExtractiveSummarizer())
        summary, err = fb.summarize(item)
        self.assertEqual(summary.provider, "extractive")
        self.assertIn("boom", err)


if __name__ == "__main__":
    unittest.main()
