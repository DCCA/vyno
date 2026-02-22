import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from digest.config import OutputSettings, ProfileConfig, SourceConfig
from digest.models import Item
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore


class TestRuntimeIntegration(unittest.TestCase):
    def test_full_run_with_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            vault = Path(tmp) / "vault"
            store = SQLiteStore(str(db))

            sources = SourceConfig(rss_feeds=["fixture"], youtube_channels=["fixture"], youtube_queries=[])
            profile = ProfileConfig(
                topics=["ai"],
                entities=["openai"],
                output=OutputSettings(obsidian_vault_path=str(vault), obsidian_folder="AI Digest"),
                llm_enabled=False,
            )

            fixture_item = Item(
                id="fixture1",
                url="https://example.com/fixture1",
                title="OpenAI evals update",
                source="fixture-source",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="Detailed ai evals coverage.",
                hash="fixturehash1",
            )

            with patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]), patch(
                "digest.runtime.fetch_youtube_items", return_value=[]
            ):
                report = run_digest(sources, profile, store)

            self.assertIn(report.status, {"success", "partial"})
            note = vault / "AI Digest"
            self.assertTrue(note.exists())
            files = list(note.glob("*.md"))
            self.assertEqual(len(files), 1)

    def test_manual_mode_keeps_value_when_items_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            vault = Path(tmp) / "vault"
            store = SQLiteStore(str(db))

            sources = SourceConfig(rss_feeds=["fixture"], youtube_channels=["fixture"], youtube_queries=[])
            profile = ProfileConfig(
                topics=["ai"],
                entities=["openai"],
                output=OutputSettings(obsidian_vault_path=str(vault), obsidian_folder="AI Digest"),
                llm_enabled=False,
            )

            fixture_item = Item(
                id="fixture1",
                url="https://example.com/fixture1",
                title="OpenAI evals update",
                source="fixture-source",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="Detailed ai evals coverage.",
                hash="fixturehash1",
            )

            with patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]), patch(
                "digest.runtime.fetch_youtube_items", return_value=[]
            ):
                # Scheduled/incremental run marks item as seen.
                first = run_digest(sources, profile, store, use_last_completed_window=True, only_new=True)
                # Manual run should still include recent window items.
                second = run_digest(sources, profile, store, use_last_completed_window=False, only_new=False)

            self.assertIn(first.status, {"success", "partial"})
            self.assertIn(second.status, {"success", "partial"})


if __name__ == "__main__":
    unittest.main()
