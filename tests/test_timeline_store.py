import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
