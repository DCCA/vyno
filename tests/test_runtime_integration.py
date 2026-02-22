import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import sqlite3

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
            files = list(note.glob("*/*.md"))
            self.assertEqual(len(files), 1)
            conn = sqlite3.connect(db)
            row = conn.execute(
                "select provider, tags_json, topic_tags_json, format_tags_json from scores where run_id = ? limit 1",
                (report.run_id,),
            ).fetchone()
            conn.close()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "rules")

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

    def test_timestamped_mode_creates_distinct_files_same_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            vault = Path(tmp) / "vault"
            store = SQLiteStore(str(db))

            sources = SourceConfig(rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[])
            profile = ProfileConfig(
                output=OutputSettings(
                    obsidian_vault_path=str(vault),
                    obsidian_folder="AI Digest",
                    obsidian_naming="timestamped",
                ),
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
                run_digest(sources, profile, store, use_last_completed_window=False, only_new=False)
                run_digest(sources, profile, store, use_last_completed_window=False, only_new=False)

            files = sorted((vault / "AI Digest").glob("*/*.md"))
            self.assertEqual(len(files), 2)

    def test_mixed_sources_include_x_and_github(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            vault = Path(tmp) / "vault"
            store = SQLiteStore(str(db))
            sources = SourceConfig(
                rss_feeds=["fixture-rss"],
                youtube_channels=["fixture-yt"],
                youtube_queries=[],
                x_inbox_path="data/x_inbox.txt",
                github_repos=["openai/openai-cookbook"],
                github_topics=["llm"],
                github_search_queries=["repo:openai/openai-cookbook is:issue llm"],
                github_orgs=["https://github.com/vercel-labs"],
            )
            profile = ProfileConfig(
                output=OutputSettings(obsidian_vault_path=str(vault), obsidian_folder="AI Digest"),
                llm_enabled=False,
                agent_scoring_enabled=False,
            )

            rss_item = Item(
                id="rss1",
                url="https://example.com/rss1",
                title="RSS item",
                source="fixture-rss",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="rss body",
                hash="rss1",
            )
            x_item = Item(
                id="x1",
                url="https://x.com/alice/status/1",
                title="X post",
                source="x.com",
                author="alice",
                published_at=datetime.now(),
                type="x_post",
                raw_text="x body",
                hash="x1",
            )
            gh_item = Item(
                id="gh1",
                url="https://github.com/openai/openai-cookbook/issues/1",
                title="GH issue",
                source="github:openai/openai-cookbook",
                author="openai",
                published_at=datetime.now(),
                type="github_issue",
                raw_text="gh body",
                hash="gh1",
            )

            with patch("digest.runtime.fetch_rss_items", return_value=[rss_item]), patch(
                "digest.runtime.fetch_youtube_items", return_value=[]
            ), patch("digest.runtime.fetch_x_inbox_items", return_value=[x_item]), patch(
                "digest.runtime.fetch_github_items", return_value=[gh_item]
            ) as gh_mock:
                report = run_digest(sources, profile, store, use_last_completed_window=False, only_new=False)

            self.assertIn(report.status, {"success", "partial"})
            self.assertEqual(gh_mock.call_args.kwargs.get("orgs"), ["vercel-labs"])
            conn = sqlite3.connect(db)
            count = conn.execute(
                "select count(*) from scores where run_id=?",
                (report.run_id,),
            ).fetchone()[0]
            conn.close()
            self.assertGreaterEqual(count, 3)

    def test_source_segmented_render_mode_writes_segmented_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            vault = Path(tmp) / "vault"
            store = SQLiteStore(str(db))
            sources = SourceConfig(rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[])
            profile = ProfileConfig(
                output=OutputSettings(
                    obsidian_vault_path=str(vault),
                    obsidian_folder="AI Digest",
                    obsidian_naming="timestamped",
                    render_mode="source_segmented",
                ),
                llm_enabled=False,
                agent_scoring_enabled=False,
            )
            fixture_item = Item(
                id="fixture1",
                url="https://github.com/openai/openai-cookbook/releases/tag/v1",
                title="OpenAI cookbook release",
                source="github:openai/openai-cookbook",
                author=None,
                published_at=datetime.now(),
                type="github_release",
                raw_text="release note",
                hash="fixturehash1",
            )
            with patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]), patch(
                "digest.runtime.fetch_youtube_items", return_value=[]
            ):
                run_digest(sources, profile, store, use_last_completed_window=False, only_new=False)

            files = sorted((vault / "AI Digest").glob("*/*.md"))
            self.assertEqual(len(files), 1)
            content = files[0].read_text(encoding="utf-8")
            self.assertIn("## Top Highlights", content)
            self.assertIn("## GitHub", content)

    def test_runtime_passes_org_guardrails_to_github_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            vault = Path(tmp) / "vault"
            store = SQLiteStore(str(db))
            sources = SourceConfig(
                rss_feeds=[],
                youtube_channels=[],
                youtube_queries=[],
                github_orgs=["vercel-labs"],
            )
            profile = ProfileConfig(
                output=OutputSettings(obsidian_vault_path=str(vault), obsidian_folder="AI Digest"),
                llm_enabled=False,
                agent_scoring_enabled=False,
                github_min_stars=123,
                github_include_forks=True,
                github_include_archived=True,
                github_max_repos_per_org=4,
                github_max_items_per_org=9,
            )
            with patch("digest.runtime.fetch_github_items", return_value=[]) as gh_mock:
                run_digest(sources, profile, store, use_last_completed_window=False, only_new=False)
            opts = gh_mock.call_args.kwargs.get("org_options") or {}
            self.assertEqual(opts.get("min_stars"), 123)
            self.assertTrue(opts.get("include_forks"))
            self.assertTrue(opts.get("include_archived"))
            self.assertEqual(opts.get("max_repos_per_org"), 4)
            self.assertEqual(opts.get("max_items_per_org"), 9)


if __name__ == "__main__":
    unittest.main()
