import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from digest.models import Item
from digest.ops.source_registry import source_key_for
from digest.storage.sqlite_store import SQLiteStore
from digest.web.app import WebSettings, create_app


class TestWebSourcePreviews(unittest.TestCase):
    def _source_preview_endpoint(self, *, sources_yaml: str, store_setup):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            sources_path = tmp_path / "sources.yaml"
            sources_path.write_text(sources_yaml, encoding="utf-8")
            profile_path = tmp_path / "profile.yaml"
            profile_path.write_text("output:\n  obsidian_vault_path: ''\n  obsidian_folder: 'AI Digest'\n", encoding="utf-8")
            settings = WebSettings(
                sources_path=str(sources_path),
                sources_overlay_path=str(tmp_path / "sources.local.yaml"),
                profile_path=str(profile_path),
                profile_overlay_path=str(tmp_path / "profile.local.yaml"),
                db_path=str(tmp_path / "digest.db"),
                run_lock_path=str(tmp_path / "run.lock"),
                history_dir=str(tmp_path / "history"),
                onboarding_state_path=str(tmp_path / "onboarding-state.json"),
            )
            store = SQLiteStore(settings.db_path)
            store_setup(store)
            app = create_app(settings)
            routes = [route for route in app.routes if getattr(route, "path", None)]
            for route in routes:
                methods = set(getattr(route, "methods", set()) or set())
                if str(getattr(route, "path")) == "/api/source-previews" and "GET" in methods:
                    return route.endpoint()
            raise KeyError("/api/source-previews")

    def test_source_previews_return_latest_item_preview(self):
        def store_setup(store: SQLiteStore):
            item = Item(
                id="item-1",
                url="https://example.com/article",
                title="Stored title",
                source="https://example.com/feed.xml",
                author="ops",
                published_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
                type="article",
                raw_text="Stored raw text",
                description="Stored description",
                hash="item-1-hash",
            )
            store.upsert_items([item])
            store.link_source_items(
                run_id="run-1",
                links=[
                    {
                        "source_key": source_key_for("rss", "https://example.com/feed.xml"),
                        "source_type": "rss",
                        "source_value": "https://example.com/feed.xml",
                        "item_id": "item-1",
                    }
                ],
            )

        with patch(
            "digest.web.app.fetch_link_preview_metadata",
            return_value={
                "url": "https://example.com/article",
                "resolved_url": "https://example.com/article",
                "host": "example.com",
                "title": "Preview title",
                "description": "Preview description",
                "image_url": "https://example.com/image.jpg",
                "status": "ready",
                "error": "",
            },
        ):
            payload = self._source_preview_endpoint(
                sources_yaml="rss_feeds:\n  - https://example.com/feed.xml\n",
                store_setup=store_setup,
            )

        self.assertEqual(len(payload["items"]), 1)
        row = payload["items"][0]
        self.assertEqual(row["preview_title"], "Preview title")
        self.assertEqual(row["preview_image_url"], "https://example.com/image.jpg")
        self.assertEqual(row["preview_status"], "ready")
        self.assertEqual(row["preview_url"], "https://example.com/article")

    def test_source_previews_fall_back_for_config_only_rows(self):
        payload = self._source_preview_endpoint(
            sources_yaml="rss_feeds: []\nx_inbox_path: data/x_inbox.txt\n",
            store_setup=lambda store: None,
        )
        self.assertEqual(len(payload["items"]), 1)
        row = payload["items"][0]
        self.assertEqual(row["type"], "x_inbox")
        self.assertEqual(row["preview_status"], "no_items")
        self.assertFalse(row["can_edit"])
        self.assertFalse(row["can_delete"])


if __name__ == "__main__":
    unittest.main()
