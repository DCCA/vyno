import tempfile
import unittest
from pathlib import Path

from digest.storage.sqlite_store import SQLiteStore
from digest.web.app import WebSettings, _parse_source_error, create_app


class TestWebSourceHealth(unittest.TestCase):
    def _source_health_endpoint(self, store_setup):
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
            store_setup(store)
            app = create_app(settings)
            routes = [route for route in app.routes if getattr(route, "path", None)]
            for route in routes:
                methods = set(getattr(route, "methods", set()) or set())
                if str(getattr(route, "path")) == "/api/source-health" and "GET" in methods:
                    return route.endpoint()
            raise KeyError("/api/source-health")

    def test_parse_github_403_error_has_actionable_hint(self):
        parsed = _parse_source_error(
            "github: GitHub API HTTPError: 403 (/repos/openai/openai-cookbook/releases?per_page=5)"
        )
        self.assertEqual(parsed["kind"], "github")
        self.assertIn("/repos/openai/openai-cookbook/releases", parsed["source"])
        self.assertIn("GITHUB_TOKEN", parsed["hint"])

    def test_parse_rss_error_extracts_feed_url(self):
        parsed = _parse_source_error("rss:https://news.ycombinator.com/rss: timed out")
        self.assertEqual(parsed["kind"], "rss")
        self.assertEqual(parsed["source"], "https://news.ycombinator.com/rss")
        self.assertIn("Feed", parsed["hint"])

    def test_parse_x_selector_errors(self):
        author = _parse_source_error("x_author:openai: HTTP Error 401")
        self.assertEqual(author["kind"], "x_author")
        self.assertEqual(author["source"], "openai")
        self.assertIn("X_BEARER_TOKEN", author["hint"])

        theme = _parse_source_error("x_theme:ai agents: HTTP Error 429")
        self.assertEqual(theme["kind"], "x_theme")
        self.assertEqual(theme["source"], "ai agents")
        self.assertIn("recent-search", theme["hint"])

    def test_source_health_uses_only_latest_completed_run(self):
        def store_setup(store: SQLiteStore):
            store.start_run("older", "2026-03-01T00:00:00+00:00", "2026-03-01T01:00:00+00:00")
            store.finish_run(
                "older",
                "partial",
                ["rss:https://news.ycombinator.com/rss: timed out"],
                [],
            )
            store.start_run("latest", "2026-03-02T00:00:00+00:00", "2026-03-02T01:00:00+00:00")
            store.finish_run(
                "latest",
                "partial",
                ["rss:https://openai.com/news/rss.xml: timed out"],
                [],
            )

        payload = self._source_health_endpoint(store_setup)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["source"], "https://openai.com/news/rss.xml")
        self.assertEqual(payload["items"][0]["last_run_id"], "latest")

    def test_source_health_clears_when_latest_completed_run_is_clean(self):
        def store_setup(store: SQLiteStore):
            store.start_run("older", "2026-03-01T00:00:00+00:00", "2026-03-01T01:00:00+00:00")
            store.finish_run(
                "older",
                "partial",
                ["rss:https://news.ycombinator.com/rss: timed out"],
                [],
            )
            store.start_run("latest", "2026-03-02T00:00:00+00:00", "2026-03-02T01:00:00+00:00")
            store.finish_run("latest", "success", [], [])

        payload = self._source_health_endpoint(store_setup)
        self.assertEqual(payload["items"], [])

    def test_source_health_aggregates_duplicate_errors_within_latest_run(self):
        def store_setup(store: SQLiteStore):
            store.start_run("latest", "2026-03-02T00:00:00+00:00", "2026-03-02T01:00:00+00:00")
            store.finish_run(
                "latest",
                "partial",
                [
                    "rss:https://news.ycombinator.com/rss: timed out",
                    "rss:https://news.ycombinator.com/rss: timed out",
                ],
                [],
            )

        payload = self._source_health_endpoint(store_setup)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["count"], 2)

    def test_source_health_returns_empty_when_no_completed_run_exists(self):
        payload = self._source_health_endpoint(lambda store: None)
        self.assertEqual(payload["items"], [])


if __name__ == "__main__":
    unittest.main()
