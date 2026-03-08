import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from digest.models import Item
from digest.storage.sqlite_store import SQLiteStore


class TestSourcePreviewStore(unittest.TestCase):
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

    def test_link_preview_cache_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            store.upsert_link_preview(
                url="https://example.com/item",
                resolved_url="https://example.com/item",
                host="example.com",
                title="Preview title",
                description="Preview description",
                image_url="https://example.com/image.jpg",
                status="ready",
            )

            preview = store.get_cached_link_preview("https://example.com/item")
            self.assertIsNotNone(preview)
            self.assertEqual(preview["title"], "Preview title")
            self.assertEqual(preview["image_url"], "https://example.com/image.jpg")


if __name__ == "__main__":
    unittest.main()
