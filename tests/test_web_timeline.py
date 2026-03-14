import tempfile
import unittest
from pathlib import Path

from digest.models import Item
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
            artifact_dir = tmp_path / ".runtime" / "run-artifacts" / run_id
            artifact_dir.mkdir(parents=True, exist_ok=True)
            telegram_artifact = artifact_dir / "telegram.json"
            telegram_artifact.write_text('["chunk one", "chunk two"]', encoding="utf-8")
            store.upsert_items(
                [
                    Item(
                        id="item-1",
                        url="https://example.com/post",
                        title="Benchmark roundup",
                        source="https://example.com/feed.xml",
                        author="alice",
                        published_at=None,
                        type="article",
                        raw_text="benchmark benchmark inference latency",
                        description="A technical benchmark item",
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
                        "score_total": 88,
                        "summary": "Review this benchmark article",
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
                storage_path=str(telegram_artifact),
                preview_mode=False,
                chunk_count=2,
            )
            store.finish_run(run_id, "success", [], [])
            store.mark_seen(["seen-a", "seen-b"])
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

            run_items = _route("/api/run-items", "GET").endpoint(run_id=run_id)
            self.assertEqual(len(run_items["items"]), 1)
            self.assertEqual(run_items["items"][0]["item_id"], "item-1")

            run_artifacts = _route("/api/run-artifacts", "GET").endpoint(run_id=run_id)
            self.assertEqual(len(run_artifacts["artifacts"]), 1)
            self.assertIn("chunk one", run_artifacts["artifacts"][0]["content"])

            archived_runs = _route("/api/run-artifacts/list", "GET").endpoint(limit=10)
            self.assertEqual(archived_runs["runs"][0]["run_id"], run_id)

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
            self.assertIn("strictness_level", summary["summary"])

            policy = _route("/api/config/run-policy", "GET").endpoint()
            self.assertIn("run_policy", policy)
            saved_policy = _route("/api/config/run-policy", "POST").endpoint(
                payload={"default_mode": "balanced", "allow_run_override": False}
            )
            self.assertTrue(saved_policy["saved"])
            self.assertEqual(saved_policy["run_policy"]["default_mode"], "balanced")
            self.assertFalse(saved_policy["run_policy"]["allow_run_override"])

            preview = _route("/api/seen/reset/preview", "POST").endpoint(
                payload={"older_than_days": 1}
            )
            self.assertIn("affected_count", preview)
            applied = _route("/api/seen/reset/apply", "POST").endpoint(
                payload={"confirm": True, "older_than_days": 1}
            )
            self.assertTrue(applied["applied"])
            self.assertIn("deleted_count", applied)

            item_feedback = _route("/api/feedback/item", "POST").endpoint(
                payload={
                    "run_id": run_id,
                    "item_id": "item-1",
                    "label": "too_technical",
                }
            )
            self.assertTrue(item_feedback["saved"])
            self.assertEqual(item_feedback["rating"], 1)

            source_feedback = _route("/api/feedback/source", "POST").endpoint(
                payload={
                    "source_type": "rss",
                    "source_value": "https://example.com/feed.xml",
                    "label": "less_source",
                }
            )
            self.assertTrue(source_feedback["saved"])

            feedback_summary = _route("/api/feedback/summary", "GET").endpoint(limit=10)
            self.assertTrue(feedback_summary["ratings"])
            self.assertEqual(feedback_summary["recent"][0]["label"], "less_source")


if __name__ == "__main__":
    unittest.main()
