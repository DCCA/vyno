import unittest
from datetime import datetime

from digest.models import Item, Summary
from digest.pipeline.summarize import FallbackSummarizer, is_low_signal_summary
from digest.summarizers.extractive import ExtractiveSummarizer


class _Primary:
    def __init__(self, summary: Summary) -> None:
        self._summary = summary

    def summarize(self, item):
        return self._summary


class TestSummaryValidation(unittest.TestCase):
    def test_rejects_too_many_urls(self):
        s = Summary(tldr="https://a.com https://b.com https://c.com", key_points=[], why_it_matters="x")
        self.assertTrue(is_low_signal_summary(s))

    def test_rejects_hashtag_spam(self):
        s = Summary(tldr="#a #b #c #d #e #f", key_points=[], why_it_matters="x")
        self.assertTrue(is_low_signal_summary(s))

    def test_rejects_sponsor_phrases(self):
        s = Summary(tldr="Check out our patreon and sponsor", key_points=[], why_it_matters="x")
        self.assertTrue(is_low_signal_summary(s))

    def test_rejects_overlong_single_line_dump(self):
        s = Summary(tldr="x" * 700, key_points=[], why_it_matters="x")
        self.assertTrue(is_low_signal_summary(s))

    def test_accepts_concise_summary(self):
        s = Summary(tldr="New benchmark improves agent reliability.", key_points=["a"], why_it_matters="Useful for evals")
        self.assertFalse(is_low_signal_summary(s))

    def test_fallback_used_when_low_signal(self):
        item = Item("1", "u", "title", "src", None, datetime.now(), "video", "Clean technical text")
        bad = Summary(tldr="Check out sponsor https://a.com https://b.com", key_points=[], why_it_matters="x")
        fb = FallbackSummarizer(primary=_Primary(bad), fallback=ExtractiveSummarizer())
        summary, err = fb.summarize(item)
        self.assertEqual(summary.provider, "extractive")
        self.assertIn("low_signal_summary", err or "")


if __name__ == "__main__":
    unittest.main()
