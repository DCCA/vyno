import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import sqlite3

from digest.config import OutputSettings, ProfileConfig, SourceConfig
from digest.models import Item, Score, Summary
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore


class TestRuntimeIntegration(unittest.TestCase):
    def test_progress_callback_emits_start_and_finish(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            profile = ProfileConfig(
                output=OutputSettings(
                    obsidian_vault_path="", obsidian_folder="AI Digest"
                ),
                llm_enabled=False,
                agent_scoring_enabled=False,
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

            events: list[dict] = []

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                    progress_cb=lambda event: events.append(event),
                )

            self.assertIn(report.status, {"success", "partial"})
            stages = [str(e.get("stage", "")) for e in events]
            self.assertIn("run_start", stages)
            self.assertIn("run_finish", stages)
            self.assertIn("score", stages)
            self.assertIn("score_progress", stages)
            self.assertIn("summarize_progress", stages)

    def test_full_run_with_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            vault = Path(tmp) / "vault"
            store = SQLiteStore(str(db))

            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=["fixture"], youtube_queries=[]
            )
            profile = ProfileConfig(
                topics=["ai"],
                entities=["openai"],
                output=OutputSettings(
                    obsidian_vault_path=str(vault), obsidian_folder="AI Digest"
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

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
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

    def test_preview_mode_skips_delivery_and_artifact_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            vault = Path(tmp) / "vault"
            store = SQLiteStore(str(db))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            profile = ProfileConfig(
                output=OutputSettings(
                    telegram_bot_token="token",
                    telegram_chat_id="chat",
                    obsidian_vault_path=str(vault),
                    obsidian_folder="AI Digest",
                ),
                llm_enabled=False,
                agent_scoring_enabled=False,
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

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
                patch("digest.runtime.send_telegram_message") as send_mock,
                patch("digest.runtime.write_obsidian_note") as write_note_mock,
                patch(
                    "digest.runtime._write_latest_telegram_artifact"
                ) as artifact_mock,
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                    preview_mode=True,
                )

            self.assertIn(report.status, {"success", "partial"})
            self.assertGreaterEqual(len(report.telegram_messages), 1)
            self.assertIn("AI Digest", report.obsidian_note)
            send_mock.assert_not_called()
            write_note_mock.assert_not_called()
            artifact_mock.assert_not_called()

    def test_manual_mode_keeps_value_when_items_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            vault = Path(tmp) / "vault"
            store = SQLiteStore(str(db))

            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=["fixture"], youtube_queries=[]
            )
            profile = ProfileConfig(
                topics=["ai"],
                entities=["openai"],
                output=OutputSettings(
                    obsidian_vault_path=str(vault), obsidian_folder="AI Digest"
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

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
            ):
                # Scheduled/incremental run marks item as seen.
                first = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=True,
                    only_new=True,
                )
                # Manual run should still include recent window items.
                second = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertIn(first.status, {"success", "partial"})
            self.assertIn(second.status, {"success", "partial"})

    def test_timestamped_mode_creates_distinct_files_same_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            vault = Path(tmp) / "vault"
            store = SQLiteStore(str(db))

            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
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

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
            ):
                run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )
                run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

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
                output=OutputSettings(
                    obsidian_vault_path=str(vault), obsidian_folder="AI Digest"
                ),
                llm_enabled=False,
                agent_scoring_enabled=False,
                trusted_orgs_github=["openai"],
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
                title="Regression issue",
                source="github:openai/openai-cookbook",
                author="openai",
                published_at=datetime.now(),
                type="github_issue",
                raw_text="incident with degraded auth flow",
                hash="gh1",
            )

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[rss_item]),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
                patch("digest.runtime.fetch_x_inbox_items", return_value=[x_item]),
                patch(
                    "digest.runtime.fetch_github_items", return_value=[gh_item]
                ) as gh_mock,
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

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
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
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
            with (
                patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
            ):
                run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

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
                output=OutputSettings(
                    obsidian_vault_path=str(vault), obsidian_folder="AI Digest"
                ),
                llm_enabled=False,
                agent_scoring_enabled=False,
                github_min_stars=123,
                github_include_forks=True,
                github_include_archived=True,
                github_max_repos_per_org=4,
                github_max_items_per_org=9,
                github_repo_max_age_days=21,
                github_activity_max_age_days=5,
            )
            with patch("digest.runtime.fetch_github_items", return_value=[]) as gh_mock:
                run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )
            opts = gh_mock.call_args.kwargs.get("org_options") or {}
            self.assertEqual(opts.get("min_stars"), 123)
            self.assertTrue(opts.get("include_forks"))
            self.assertTrue(opts.get("include_archived"))
            self.assertEqual(opts.get("max_repos_per_org"), 4)
            self.assertEqual(opts.get("max_items_per_org"), 9)
            self.assertEqual(opts.get("repo_max_age_days"), 21)
            self.assertEqual(opts.get("activity_max_age_days"), 5)

    def test_llm_summarization_is_limited_to_selected_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            profile = ProfileConfig(
                llm_enabled=True,
                agent_scoring_enabled=False,
                max_llm_summaries_per_run=20,
            )

            fixture_items = [
                Item(
                    id=f"fixture-{idx}",
                    url=f"https://example.com/{idx}",
                    title=f"AI update {idx}",
                    source="fixture-source",
                    author=None,
                    published_at=datetime.now(),
                    type="article",
                    raw_text=f"Detailed coverage {idx}",
                    hash=f"fixture-hash-{idx}",
                )
                for idx in range(60)
            ]
            llm_summary_calls: list[str] = []

            class _FakeLLMSummarizer:
                def __init__(self, *args, **kwargs):
                    pass

                def summarize(self, item: Item) -> Summary:
                    llm_summary_calls.append(item.id)
                    return Summary(
                        tldr=f"Summary for {item.id}",
                        key_points=["point"],
                        why_it_matters="matters",
                        provider="openai_responses",
                    )

            with (
                patch("digest.runtime.fetch_rss_items", return_value=fixture_items),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
                patch("digest.runtime.ResponsesAPISummarizer", _FakeLLMSummarizer),
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertIn(report.status, {"success", "partial"})
            selected_count = (
                report.must_read_count + report.skim_count + report.video_count
            )
            self.assertEqual(len(llm_summary_calls), min(selected_count, 20))

    def test_llm_request_budget_caps_scoring_and_summary_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            profile = ProfileConfig(
                llm_enabled=True,
                agent_scoring_enabled=True,
                max_agent_items_per_run=10,
                max_llm_summaries_per_run=20,
                max_llm_requests_per_run=5,
                quality_repair_enabled=False,
            )

            fixture_items = [
                Item(
                    id=f"budget-{idx}",
                    url=f"https://example.com/budget-{idx}",
                    title=f"Budget item {idx}",
                    source="fixture-source",
                    author=None,
                    published_at=datetime.now(),
                    type="article",
                    raw_text=f"Budget text {idx}",
                    hash=f"budget-hash-{idx}",
                )
                for idx in range(40)
            ]

            score_calls: list[str] = []
            summary_calls: list[str] = []

            class _FakeScorer:
                def __init__(self, *args, **kwargs):
                    pass

                def score_and_tag(
                    self, item: Item, *, max_text_chars: int = 8000
                ) -> Score:
                    score_calls.append(item.id)
                    return Score(
                        item_id=item.id,
                        relevance=60,
                        quality=20,
                        novelty=5,
                        total=85,
                        reason="fake",
                        tags=["llm"],
                        topic_tags=["llm"],
                        format_tags=["news"],
                        provider="agent",
                    )

            class _FakeLLMSummarizer:
                def __init__(self, *args, **kwargs):
                    pass

                def summarize(self, item: Item) -> Summary:
                    summary_calls.append(item.id)
                    return Summary(
                        tldr=f"Summary for {item.id}",
                        key_points=["point"],
                        why_it_matters="matters",
                        provider="openai_responses",
                    )

            with (
                patch("digest.runtime.fetch_rss_items", return_value=fixture_items),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
                patch("digest.runtime.ResponsesAPIScorerTagger", _FakeScorer),
                patch("digest.runtime.ResponsesAPISummarizer", _FakeLLMSummarizer),
            ):
                run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertEqual(len(score_calls), 5)
            self.assertEqual(len(summary_calls), 0)

    def test_incremental_mode_can_disable_seen_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            profile = ProfileConfig(llm_enabled=False, agent_scoring_enabled=False)

            fixture_item = Item(
                id="seen-item",
                url="https://example.com/seen-item",
                title="Seen item",
                source="fixture-source",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="seen item text",
                hash="seen-item-hash",
            )

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
            ):
                run_digest(
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
                    only_new=True,
                    allow_seen_fallback=False,
                )

            self.assertEqual(second.source_count, 0)
            self.assertEqual(second.must_read_count, 0)
            self.assertEqual(second.skim_count, 0)
            self.assertEqual(second.video_count, 0)

    def test_incremental_mode_supplements_seen_videos_when_none_new(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            sources = SourceConfig(
                rss_feeds=["fixture-rss"],
                youtube_channels=["fixture-yt"],
                youtube_queries=[],
            )
            profile = ProfileConfig(llm_enabled=False, agent_scoring_enabled=False)

            seen_article = Item(
                id="seen-article",
                url="https://example.com/seen-article",
                title="Seen article",
                source="fixture-rss",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="seen article",
                hash="seen-article-hash",
            )
            seen_video = Item(
                id="seen-video",
                url="https://youtube.com/watch?v=seen",
                title="Seen video",
                source="youtube.com",
                author=None,
                published_at=datetime.now(),
                type="video",
                raw_text="seen video",
                hash="seen-video-hash",
            )
            new_article = Item(
                id="new-article",
                url="https://example.com/new-article",
                title="New article",
                source="fixture-rss",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="new article",
                hash="new-article-hash",
            )

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[seen_article]),
                patch("digest.runtime.fetch_youtube_items", return_value=[seen_video]),
            ):
                run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[new_article]),
                patch("digest.runtime.fetch_youtube_items", return_value=[seen_video]),
            ):
                second = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=True,
                    allow_seen_fallback=False,
                )

            self.assertEqual(second.source_count, 2)
            self.assertGreaterEqual(second.video_count, 1)
            self.assertIn("filtering", second.context)
            self.assertIn("video_funnel", second.context)
            self.assertEqual(second.context["video_funnel"]["selected"], second.video_count)
            self.assertIn("dedupe_dropped", second.context["filtering"])
            self.assertGreaterEqual(second.context["filtering"]["seen_readded_videos"], 1)

    def test_runtime_filters_low_impact_github_issues(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            sources = SourceConfig(
                rss_feeds=[],
                youtube_channels=[],
                youtube_queries=[],
                github_repos=["anthropics/claude-code"],
            )
            profile = ProfileConfig(
                llm_enabled=False,
                agent_scoring_enabled=False,
                trusted_orgs_github=["anthropics"],
            )

            kept_issue = Item(
                id="issue-keep",
                url="https://github.com/anthropics/claude-code/issues/1",
                title="Regression causes outage in auth flow",
                source="github:anthropics/claude-code",
                author="maintainer",
                published_at=datetime.now(),
                type="github_issue",
                raw_text="labels=bug,incident | comments=10",
                hash="issue-keep-hash",
            )
            dropped_no_keyword = Item(
                id="issue-drop-keyword",
                url="https://github.com/anthropics/claude-code/issues/2",
                title="Small UI typo",
                source="github:anthropics/claude-code",
                author="maintainer",
                published_at=datetime.now(),
                type="github_issue",
                raw_text="labels=docs | comments=1",
                hash="issue-drop-keyword-hash",
            )
            dropped_untrusted = Item(
                id="issue-drop-untrusted",
                url="https://github.com/random/repo/issues/3",
                title="Regression causes outage",
                source="github:random/repo",
                author="maintainer",
                published_at=datetime.now(),
                type="github_issue",
                raw_text="labels=incident | comments=2",
                hash="issue-drop-untrusted-hash",
            )

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[]),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
                patch(
                    "digest.runtime.fetch_github_items",
                    return_value=[kept_issue, dropped_no_keyword, dropped_untrusted],
                ),
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertIn(report.status, {"success", "partial"})
            self.assertEqual(report.source_count, 1)

            conn = sqlite3.connect(db)
            rows = conn.execute(
                "select item_id from scores where run_id = ?",
                (report.run_id,),
            ).fetchall()
            conn.close()
            scored_ids = {row[0] for row in rows}
            self.assertIn("issue-keep", scored_ids)
            self.assertNotIn("issue-drop-keyword", scored_ids)
            self.assertNotIn("issue-drop-untrusted", scored_ids)

    def test_run_report_includes_context_feedback(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            profile = ProfileConfig(llm_enabled=False, agent_scoring_enabled=False)

            fixture_item = Item(
                id="ctx-1",
                url="https://example.com/ctx-1",
                title="Context test item",
                source="fixture-source",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="context test body",
                hash="ctx-hash-1",
            )

            with (
                patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
            ):
                report = run_digest(
                    sources,
                    profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertIsInstance(report.context, dict)
            self.assertIn("fetched", report.context)
            self.assertIn("pipeline", report.context)
            self.assertIn("filtering", report.context)
            self.assertIn("video_funnel", report.context)
            self.assertIn("selection", report.context)
            self.assertEqual(report.context["selection"]["final_item_count"], 1)
            self.assertGreaterEqual(report.context["fetched"]["raw_total"], 1)
            self.assertEqual(report.context["video_funnel"]["selected"], 0)
            self.assertIn("dedupe_dropped", report.context["filtering"])
            self.assertIn("sparse_note", report.context)


if __name__ == "__main__":
    unittest.main()
