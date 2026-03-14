import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from digest.models import Item
from digest.storage.sqlite_store import SQLiteStore


class TestTimelineStore(unittest.TestCase):
    def test_timeline_events_filters_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            run_id = "run-1"
            store.start_run(run_id, "2026-03-01T00:00:00+00:00", "2026-03-01T01:00:00+00:00")
            store.insert_timeline_event(
                run_id=run_id,
                event_index=1,
                stage="fetch_rss",
                severity="info",
                message="Fetched RSS",
                elapsed_s=2.1,
                details={"item_count": 10},
            )
            store.insert_timeline_event(
                run_id=run_id,
                event_index=2,
                stage="fetch_github",
                severity="error",
                message="GitHub failed",
                elapsed_s=4.7,
                details={"error": "403"},
            )
            store.insert_timeline_event(
                run_id=run_id,
                event_index=3,
                stage="run_finish",
                severity="warn",
                message="Run completed partial",
                elapsed_s=10.0,
                details={
                    "status": "partial",
                    "final_item_count": 7,
                    "must_read_count": 5,
                    "skim_count": 2,
                    "video_count": 0,
                },
            )
            store.finish_run(run_id, "partial", ["github: 403"], [])

            all_events = store.list_timeline_events(run_id=run_id, limit=50)
            self.assertEqual(len(all_events), 3)
            self.assertEqual(all_events[0]["event_index"], 1)
            self.assertEqual(all_events[-1]["stage"], "run_finish")

            only_errors = store.list_timeline_events(
                run_id=run_id,
                severity="error",
                limit=20,
            )
            self.assertEqual(len(only_errors), 1)
            self.assertEqual(only_errors[0]["stage"], "fetch_github")

            after_one = store.list_timeline_events(
                run_id=run_id,
                after_event_index=1,
                limit=20,
            )
            self.assertEqual(len(after_one), 2)
            desc_events = store.list_timeline_events(
                run_id=run_id,
                limit=20,
                order="desc",
            )
            self.assertEqual(desc_events[0]["event_index"], 3)
            self.assertEqual(desc_events[-1]["event_index"], 1)

            summary = store.timeline_summary(run_id=run_id)
            self.assertEqual(summary["run_id"], run_id)
            self.assertEqual(summary["status"], "partial")
            self.assertEqual(summary["event_count"], 3)
            self.assertEqual(summary["error_event_count"], 1)
            self.assertEqual(summary["warn_event_count"], 1)
            self.assertEqual(summary["final_item_count"], 7)
            self.assertEqual(summary["must_read_count"], 5)
            self.assertEqual(summary["skim_count"], 2)
            self.assertEqual(summary["video_count"], 0)
            self.assertEqual(summary["source_error_count"], 1)
            self.assertIn(summary["strictness_level"], {"low", "medium", "high"})
            self.assertIn("filter_funnel", summary)
            self.assertIn("recommendations", summary)

            export_payload = store.export_timeline(run_id=run_id)
            self.assertEqual(export_payload["run_id"], run_id)
            self.assertEqual(len(export_payload["events"]), 3)
            self.assertIn("summary", export_payload)

    def test_timeline_notes_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            run_id = "run-notes"
            store.start_run(run_id, "2026-03-01T00:00:00+00:00", "2026-03-01T01:00:00+00:00")
            note_id = store.add_timeline_note(
                run_id=run_id,
                author="ops",
                note="Investigate recurring GitHub 403 errors.",
                labels=["github", "auth"],
                actions=["rotate token"],
            )
            self.assertGreater(note_id, 0)
            notes = store.list_timeline_notes(run_id=run_id, limit=20)
            self.assertEqual(len(notes), 1)
            self.assertEqual(notes[0]["author"], "ops")
            self.assertEqual(notes[0]["labels"], ["github", "auth"])
            self.assertEqual(notes[0]["actions"], ["rotate token"])

    def test_timeline_runs_include_orphan_event_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            orphan_run_id = "web-request-run"
            store.insert_timeline_event(
                run_id=orphan_run_id,
                event_index=0,
                stage="queued",
                severity="info",
                message="Queued digest run",
                elapsed_s=0.0,
                details={"mode": "live"},
            )
            rows = store.list_timeline_runs(limit=10)
            self.assertEqual(rows[0]["run_id"], orphan_run_id)
            self.assertEqual(rows[0]["event_count"], 1)
            self.assertIn(rows[0]["status"], {"running", "unknown"})
            summary = store.timeline_summary(run_id=orphan_run_id)
            self.assertEqual(summary["run_id"], orphan_run_id)
            self.assertEqual(summary["event_count"], 1)

    def test_reassign_timeline_run_id_moves_events_and_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            old_run_id = "web-request-run"
            new_run_id = "pipeline-run"
            store.insert_timeline_event(
                run_id=old_run_id,
                event_index=0,
                stage="queued",
                severity="info",
                message="Queued digest run",
                elapsed_s=0.0,
                details={"mode": "live"},
            )
            store.add_timeline_note(run_id=old_run_id, note="note", author="ops")
            store.reassign_timeline_run_id(old_run_id=old_run_id, new_run_id=new_run_id)

            old_events = store.list_timeline_events(run_id=old_run_id, limit=10)
            new_events = store.list_timeline_events(run_id=new_run_id, limit=10)
            self.assertEqual(len(old_events), 0)
            self.assertEqual(len(new_events), 1)

            old_notes = store.list_timeline_notes(run_id=old_run_id, limit=10)
            new_notes = store.list_timeline_notes(run_id=new_run_id, limit=10)
            self.assertEqual(len(old_notes), 0)
            self.assertEqual(len(new_notes), 1)

    def test_seen_reset_preview_and_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            store.mark_seen(["a", "b", "c"])
            preview_all = store.preview_seen_reset()
            self.assertEqual(preview_all, 3)
            deleted = store.reset_seen()
            self.assertEqual(deleted, 3)
            self.assertEqual(store.preview_seen_reset(), 0)

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


if __name__ == "__main__":
    unittest.main()
