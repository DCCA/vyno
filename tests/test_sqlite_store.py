import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from digest.models import Item
from digest.storage.sqlite_store import SQLiteStore


class TestSQLiteStore(unittest.TestCase):
    def test_seen_reset_clears_all_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            store.mark_seen(["a", "b", "c"])
            self.assertEqual(store.reset_seen(), 3)
            self.assertEqual(store.seen_keys(), set())

    def test_x_selector_cursor_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            self.assertIsNone(store.get_x_cursor("x_author", "openai"))

            store.set_x_cursor(
                selector_type="x_author",
                selector_value="openai",
                cursor="abc-next",
                last_item_id="12345",
            )
            self.assertEqual(store.get_x_cursor("x_author", "openai"), "abc-next")

            store.set_x_cursor(
                selector_type="x_author",
                selector_value="openai",
                cursor="def-next",
                last_item_id="22222",
            )
            self.assertEqual(store.get_x_cursor("x_author", "openai"), "def-next")

    def test_run_archive_and_feedback_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            artifact = Path(tmp) / "telegram.json"
            artifact.write_text('["hello"]', encoding="utf-8")
            store = SQLiteStore(str(db))
            run_id = "run-archive"
            store.start_run(run_id, "2026-03-01T00:00:00+00:00", "2026-03-01T01:00:00+00:00")
            store.upsert_items(
                [
                    Item(
                        id="item-1",
                        url="https://example.com/item-1",
                        title="Inference benchmark notes",
                        source="https://example.com/feed.xml",
                        author="alice",
                        published_at=datetime.fromisoformat("2026-03-01T00:00:00+00:00"),
                        type="article",
                        raw_text="Benchmark coverage for model inference latency",
                        description="A benchmark-heavy article",
                    )
                ]
            )
            store.replace_run_selected_items(
                run_id,
                [
                    {
                        "item_id": "item-1",
                        "section": "must_read",
                        "section_rank": 1,
                        "source_family": "example.com",
                        "score_total": 91,
                        "raw_total": 93,
                        "adjusted_total": 91,
                        "adjustment_breakdown": {
                            "source_preference": 2.0,
                            "research_balance": -4.0,
                        },
                        "summary": "Strong benchmark-heavy item",
                        "tags": ["benchmark", "technical"],
                        "topic_tags": ["infra"],
                        "format_tags": ["technical"],
                    }
                ],
            )
            store.upsert_run_artifact(
                run_id=run_id,
                channel="telegram",
                artifact_type="message_bundle",
                storage_path=str(artifact),
                preview_mode=False,
                chunk_count=1,
            )
            store.add_feedback(
                run_id=run_id,
                item_id="item-1",
                rating=1,
                label="too_technical",
                comment="too dense",
                target_kind="item",
                target_key="item-1",
                features=[("technicality", "high"), ("source", "example.com")],
                actor="tester",
            )

            run_items = store.list_run_items(run_id=run_id)
            artifacts = store.list_run_artifacts(run_id=run_id)
            archived_runs = store.list_archived_runs(limit=10)
            summary = store.feedback_summary()
            bias = store.feedback_feature_bias()

            self.assertEqual(len(run_items), 1)
            self.assertEqual(run_items[0]["item_id"], "item-1")
            self.assertEqual(run_items[0]["score_total"], 91)
            self.assertEqual(run_items[0]["raw_total"], 93)
            self.assertEqual(run_items[0]["adjusted_total"], 91)
            self.assertEqual(run_items[0]["score_mode"], "adjusted")
            self.assertEqual(
                run_items[0]["adjustment_breakdown"]["research_balance"], -4.0
            )
            self.assertEqual(len(artifacts), 1)
            self.assertEqual(artifacts[0]["channel"], "telegram")
            self.assertEqual(archived_runs[0]["run_id"], run_id)
            self.assertEqual(summary[0], (1, 1))
            self.assertLess(bias[("technicality", "high")], 0.0)

    def test_ingest_suggestion_rows_are_excluded_from_summary_and_bias(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "digest.db"))
            store.add_feedback(
                run_id="",
                item_id="",
                rating=5,
                label="rated",
                comment="great",
                target_kind="item",
                target_key="item-1",
                features=[("source", "example.com")],
            )
            store.add_feedback(
                run_id="",
                item_id="",
                rating=0,
                label="ingest_suggestion",
                comment="no feed found",
                target_kind="ingest",
                target_key="https://pod.example.com/show",
                features=[("source", "example.com")],
            )

            self.assertEqual(store.feedback_summary(), [(5, 1)])
            self.assertGreater(
                store.feedback_feature_bias()[("source", "example.com")], 0.0
            )
            self.assertEqual(len(store.list_feedback()), 2)

    def test_list_run_items_falls_back_for_legacy_score_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            run_id = "legacy-run"
            store.start_run(run_id, "2026-03-01T00:00:00+00:00", "2026-03-01T01:00:00+00:00")
            store.upsert_items(
                [
                    Item(
                        id="legacy-item",
                        url="https://example.com/legacy",
                        title="Legacy score row",
                        source="https://example.com/feed.xml",
                        author="alice",
                        published_at=datetime.fromisoformat("2026-03-01T00:00:00+00:00"),
                        type="article",
                        raw_text="legacy row",
                        description="old row",
                    )
                ]
            )
            with store._conn() as conn:
                conn.execute(
                    (
                        "INSERT INTO run_selected_items "
                        "(run_id, item_id, section, section_rank, source_family, score_total, raw_total, adjusted_total, "
                        "adjustment_breakdown_json, summary, tags_json, topic_tags_json, format_tags_json) "
                        "VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, '', ?, '[]', '[]', '[]')"
                    ),
                    (
                        run_id,
                        "legacy-item",
                        "must_read",
                        1,
                        "example.com",
                        77,
                        "legacy summary",
                    ),
                )

            run_items = store.list_run_items(run_id=run_id)

            self.assertEqual(run_items[0]["score_total"], 77)
            self.assertEqual(run_items[0]["raw_total"], 77)
            self.assertEqual(run_items[0]["adjusted_total"], 77)
            self.assertEqual(run_items[0]["score_mode"], "legacy_raw")

    def test_latest_items_for_sources_returns_most_recent_linked_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            older = Item(
                id="older",
                url="https://example.com/older",
                title="Older item",
                source="rss-source",
                author="ops",
                published_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                type="article",
                raw_text="older body",
                description="older summary",
                hash="older-hash",
            )
            newer = Item(
                id="newer",
                url="https://example.com/newer",
                title="Newer item",
                source="rss-source",
                author="ops",
                published_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
                type="article",
                raw_text="newer body",
                description="newer summary",
                hash="newer-hash",
            )
            store.upsert_items([older, newer])
            store.link_source_items(
                run_id="run-1",
                links=[
                    {
                        "source_key": "rss:https://example.com/feed.xml",
                        "source_type": "rss",
                        "source_value": "https://example.com/feed.xml",
                        "item_id": "older",
                    },
                    {
                        "source_key": "rss:https://example.com/feed.xml",
                        "source_type": "rss",
                        "source_value": "https://example.com/feed.xml",
                        "item_id": "newer",
                    },
                ],
            )

            latest = store.latest_items_for_sources(["rss:https://example.com/feed.xml"])
            self.assertEqual(latest["rss:https://example.com/feed.xml"]["item_id"], "newer")
            self.assertEqual(latest["rss:https://example.com/feed.xml"]["description"], "newer summary")


if __name__ == "__main__":
    unittest.main()
