import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from digest.config import OutputSettings, ProfileConfig, SourceConfig
from digest.llm.client import is_terminal_error
from digest.models import Item
from digest.runtime import _classify_fallback_reason, run_digest
from digest.storage.sqlite_store import SQLiteStore

QUOTA_ERROR = (
    "Agent scoring failed: Error code: 429 - {'error': {'message': 'You have no "
    "credits remaining. Add credits to continue using the API at "
    "https://platform.openai.com/settings/organization/billing/.', 'type': "
    "'insufficient_quota', 'param': None, 'code': 'credit_balance_exhausted'}}"
)


class _QuotaExhaustedScorer:
    """Counts every call so the test can prove we stop calling a dead API."""

    instances: list["_QuotaExhaustedScorer"] = []

    def __init__(self, model: str = "x", timeout: int = 30) -> None:
        _ = model, timeout
        self.calls = 0
        _QuotaExhaustedScorer.instances.append(self)

    def score_and_tag(self, item, *, max_text_chars: int = 8000):
        _ = item, max_text_chars
        self.calls += 1
        raise RuntimeError(QUOTA_ERROR)


class TestTerminalErrorDetection(unittest.TestCase):
    def test_quota_exhaustion_is_terminal(self):
        self.assertTrue(is_terminal_error(QUOTA_ERROR))
        self.assertTrue(is_terminal_error(RuntimeError(QUOTA_ERROR)))

    def test_transient_errors_are_not_terminal(self):
        self.assertFalse(is_terminal_error("Error code: 429 - rate limit reached"))
        self.assertFalse(is_terminal_error("Agent scoring timeout"))
        self.assertFalse(is_terminal_error(""))
        self.assertFalse(is_terminal_error(None))

    def test_quota_exhaustion_classifies_apart_from_rate_limit(self):
        self.assertEqual(_classify_fallback_reason(QUOTA_ERROR), "quota_exhausted")
        self.assertEqual(
            _classify_fallback_reason("Error code: 429 - rate limit reached"),
            "rate_limit",
        )


class TestTerminalErrorStopsLLMCalls(unittest.TestCase):
    def _item(self, item_id: str) -> Item:
        return Item(
            id=item_id,
            url=f"https://example.com/{item_id}",
            title=f"AI item {item_id}",
            source="example.com",
            author=None,
            published_at=datetime.now(),
            type="article",
            raw_text="AI content for scoring.",
            hash=f"h-{item_id}",
        )

    def test_quota_error_stops_agent_scoring_for_the_whole_run(self):
        _QuotaExhaustedScorer.instances = []
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "digest.db"))
            sources = SourceConfig(rss_feeds=["fixture"], youtube_channels=[])
            profile = ProfileConfig(
                output=OutputSettings(
                    obsidian_vault_path="", obsidian_folder="AI Digest"
                ),
                llm_enabled=False,
                agent_scoring_enabled=True,
                min_llm_coverage=0.9,
                max_fallback_share=0.1,
                agent_scoring_retry_attempts=3,
            )
            items = [self._item(f"a{n}") for n in range(5)]
            with (
                patch("digest.runtime.fetch_rss_items", return_value=items),
                patch(
                    "digest.runtime.ResponsesAPIScorerTagger", _QuotaExhaustedScorer
                ),
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            calls = sum(s.calls for s in _QuotaExhaustedScorer.instances)
            # 5 items x 4 attempts each = 20 calls if nothing short-circuits.
            self.assertEqual(calls, 1)
            self.assertEqual(report.status, "partial")
            joined = "\n".join(report.summary_errors)
            self.assertIn("quota_exhausted", joined)
            self.assertNotIn("rate_limit", joined)


if __name__ == "__main__":
    unittest.main()
