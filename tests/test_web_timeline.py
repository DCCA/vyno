import tempfile
import unittest
from pathlib import Path

from digest.storage.sqlite_store import SQLiteStore
from digest.web.app import WebSettings, create_app


class TestWebTimeline(unittest.TestCase):
    def _app(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            db_path = tmp_path / "digest.db"
            settings = WebSettings(
                sources_path=str(root / "config" / "sources.yaml"),
                sources_overlay_path=str(tmp_path / "sources.local.yaml"),
                profile_path=str(root / "config" / "profile.yaml"),
                profile_overlay_path=str(tmp_path / "profile.local.yaml"),
                db_path=str(db_path),
                run_lock_path=str(tmp_path / "run.lock"),
                history_dir=str(tmp_path / "history"),
                onboarding_state_path=str(tmp_path / "onboarding-state.json"),
            )
            store = SQLiteStore(str(db_path))
            run_id = "timeline-web-1"
            store.start_run(run_id, "2026-03-01T00:00:00+00:00", "2026-03-01T01:00:00+00:00")
            store.insert_timeline_event(
                run_id=run_id,
                event_index=1,
                stage="run_start",
                severity="info",
                message="Digest run started",
                elapsed_s=0.2,
                details={"mode": "live"},
            )
            store.insert_timeline_event(
                run_id=run_id,
                event_index=2,
                stage="run_finish",
                severity="info",
                message="Digest run finished",
                elapsed_s=4.5,
                details={
                    "status": "success",
                    "final_item_count": 6,
                    "must_read_count": 5,
                    "skim_count": 1,
                    "video_count": 0,
                },
            )
            store.finish_run(run_id, "success", [], [])
            yield create_app(settings), run_id

    def test_timeline_endpoints_return_expected_shapes(self):
        for app, run_id in self._app():
            routes = [route for route in app.routes if getattr(route, "path", None)]

            def _route(path: str, method: str):
                for route in routes:
                    methods = set(getattr(route, "methods", set()) or set())
                    if str(getattr(route, "path")) == path and method in methods:
                        return route
                raise KeyError(f"{method} {path}")

            runs = _route("/api/timeline/runs", "GET").endpoint(limit=10)
            self.assertIn("runs", runs)
            self.assertGreaterEqual(len(runs["runs"]), 1)

            events = _route("/api/timeline/events", "GET").endpoint(
                run_id=run_id,
                limit=50,
                after_event_index=0,
                stage="",
                severity="",
                order="asc",
            )
            self.assertIn("events", events)
            self.assertEqual(len(events["events"]), 2)
            events_desc = _route("/api/timeline/events", "GET").endpoint(
                run_id=run_id,
                limit=50,
                after_event_index=0,
                stage="",
                severity="",
                order="desc",
            )
            self.assertEqual(events_desc["events"][0]["event_index"], 2)

            summary = _route("/api/timeline/summary", "GET").endpoint(run_id=run_id)
            self.assertEqual(summary["summary"]["run_id"], run_id)
            self.assertEqual(summary["summary"]["event_count"], 2)

            created = _route("/api/timeline/notes", "POST").endpoint(
                payload={"run_id": run_id, "note": "Good run", "author": "ops"}
            )
            self.assertTrue(created["created"])
            notes = _route("/api/timeline/notes", "GET").endpoint(
                run_id=run_id, limit=20
            )
            self.assertEqual(len(notes["notes"]), 1)

            export_payload = _route("/api/timeline/export", "GET").endpoint(
                run_id=run_id,
                limit_events=100,
                limit_notes=100,
            )
            self.assertEqual(export_payload["run_id"], run_id)
            self.assertIn("events", export_payload)
            self.assertIn("notes", export_payload)


if __name__ == "__main__":
    unittest.main()
