import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from digest.config import OutputSettings, ProfileConfig, SourceConfig
from digest.models import Item
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore


class _AlwaysFailScorer:
    def __init__(self, model: str = "x", timeout: int = 30) -> None:
        _ = model, timeout

    def score_and_tag(self, item, *, max_text_chars: int = 8000):
        _ = item, max_text_chars
        raise RuntimeError("Agent scoring HTTPError: 429")


class _RetryPassScorer:
    def __init__(self, model: str = "x", timeout: int = 30) -> None:
        _ = model, timeout
        self.calls: dict[str, int] = {}
        self.max_chars_used: list[int] = []

    def score_and_tag(self, item, *, max_text_chars: int = 8000):
        from digest.models import Score

        self.max_chars_used.append(max_text_chars)
        c = self.calls.get(item.id, 0) + 1
        self.calls[item.id] = c
        if c == 1:
            raise RuntimeError("Agent scoring timeout")
        return Score(
            item_id=item.id,
            relevance=10,
            quality=10,
            novelty=5,
            total=25,
            reason="ok",
            provider="agent",
        )


class _CountingPassScorer:
    def __init__(self, model: str = "x", timeout: int = 30) -> None:
        _ = model, timeout
        self.calls = 0

    def score_and_tag(self, item, *, max_text_chars: int = 8000):
        from digest.models import Score

        _ = max_text_chars
        self.calls += 1
        return Score(
            item_id=item.id,
            relevance=12,
            quality=9,
            novelty=6,
            total=27,
            reason="ok",
            provider="agent",
        )


class TestScoringCoverage(unittest.TestCase):
    def _item(self, item_id: str) -> Item:
        return Item(
            id=item_id,
            url=f"https://example.com/{item_id}",
            title=f"Item {item_id}",
            source="fixture",
            author=None,
            published_at=datetime.now(),
            type="article",
            raw_text="AI content for scoring.",
            hash=f"h-{item_id}",
        )

    def test_low_llm_coverage_marks_run_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "digest.db"))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            profile = ProfileConfig(
                output=OutputSettings(
                    obsidian_vault_path="", obsidian_folder="AI Digest"
                ),
                llm_enabled=False,
                agent_scoring_enabled=True,
                min_llm_coverage=0.9,
                max_fallback_share=0.1,
            )
            items = [self._item("a1"), self._item("a2")]
            with (
                patch("digest.runtime.fetch_rss_items", return_value=items),
                patch("digest.runtime.ResponsesAPIScorerTagger", _AlwaysFailScorer),
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertEqual(report.status, "partial")
            joined = "\n".join(report.summary_errors)
            self.assertIn("scoring_coverage_below_threshold", joined)
            self.assertIn("rate_limit", joined)

    def test_retry_with_smaller_text_limit_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "digest.db"))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            profile = ProfileConfig(
                output=OutputSettings(
                    obsidian_vault_path="", obsidian_folder="AI Digest"
                ),
                llm_enabled=False,
                agent_scoring_enabled=True,
                min_llm_coverage=0.5,
                max_fallback_share=0.5,
                agent_scoring_retry_attempts=1,
                agent_scoring_text_max_chars=8000,
            )
            items = [self._item("a1")]
            scorer = _RetryPassScorer()
            with (
                patch("digest.runtime.fetch_rss_items", return_value=items),
                patch("digest.runtime.ResponsesAPIScorerTagger", return_value=scorer),
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertIn(report.status, {"success", "partial"})
            self.assertGreaterEqual(len(scorer.max_chars_used), 2)
            self.assertEqual(scorer.max_chars_used[0], 8000)
            self.assertEqual(scorer.max_chars_used[1], 4000)

    def test_cap_overflow_does_not_fail_coverage_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "digest.db"))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            profile = ProfileConfig(
                output=OutputSettings(
                    obsidian_vault_path="", obsidian_folder="AI Digest"
                ),
                llm_enabled=False,
                agent_scoring_enabled=True,
                max_agent_items_per_run=1,
                min_llm_coverage=1.0,
                max_fallback_share=0.0,
            )
            items = [self._item("a1"), self._item("a2"), self._item("a3")]
            scorer = _CountingPassScorer()
            with (
                patch("digest.runtime.fetch_rss_items", return_value=items),
                patch("digest.runtime.ResponsesAPIScorerTagger", return_value=scorer),
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertEqual(report.status, "success")
            self.assertEqual(scorer.calls, 1)

    def test_score_cache_reuses_agent_score_on_repeat_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "digest.db"))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            profile = ProfileConfig(
                output=OutputSettings(
                    obsidian_vault_path="", obsidian_folder="AI Digest"
                ),
                llm_enabled=False,
                agent_scoring_enabled=True,
                max_agent_items_per_run=5,
                min_llm_coverage=0.0,
                max_fallback_share=1.0,
            )
            item = self._item("cache1")
            scorer = _CountingPassScorer()
            with (
                patch("digest.runtime.fetch_rss_items", return_value=[item]),
                patch("digest.runtime.ResponsesAPIScorerTagger", return_value=scorer),
            ):
                first = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )
                second = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertEqual(first.status, "success")
            self.assertEqual(second.status, "success")
            self.assertEqual(scorer.calls, 1)
            cached = store.get_cached_score(
                item.hash, profile.openai_model, item_id=item.id, max_age_hours=24
            )
            self.assertIsNotNone(cached)


if __name__ == "__main__":
    unittest.main()
