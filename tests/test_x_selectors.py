import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from digest.config import SourceConfig
from digest.connectors.x_provider import XPostPayload
from digest.connectors.x_selectors import fetch_x_selector_items
from digest.storage.sqlite_store import SQLiteStore


class _FakeProvider:
    def __init__(self):
        self.author_calls: list[tuple[str, str | None, int]] = []
        self.theme_calls: list[tuple[str, str | None, int]] = []

    def fetch_author_posts(self, *, author: str, cursor: str | None, limit: int):
        self.author_calls.append((author, cursor, limit))
        post = XPostPayload(
            id="111",
            text="Author update with link",
            author_username=author,
            created_at=datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc),
            url=f"https://x.com/{author}/status/111",
            outbound_urls=["https://example.com/article"],
        )
        return [post], "next-author-cursor"

    def fetch_theme_posts(self, *, query: str, cursor: str | None, limit: int):
        self.theme_calls.append((query, cursor, limit))
        post = XPostPayload(
            id="222",
            text="Theme update",
            author_username="newsbot",
            created_at=datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc),
            url="https://x.com/newsbot/status/222",
            outbound_urls=[],
        )
        return [post], "next-theme-cursor"


class TestXSelectors(unittest.TestCase):
    def test_inbox_only_provider_reports_selector_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "digest.db"))
            sources = SourceConfig(
                rss_feeds=["https://example.com/rss.xml"],
                x_authors=["openai"],
                x_themes=["ai agents"],
            )
            items, errors = fetch_x_selector_items(sources, store)
            self.assertEqual(items, [])
            self.assertEqual(len(errors), 2)
            self.assertTrue(any(err.startswith("x_author:openai") for err in errors))
            self.assertTrue(any(err.startswith("x_theme:ai agents") for err in errors))

    def test_selector_items_map_and_cursor_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "digest.db"))
            sources = SourceConfig(
                rss_feeds=["https://example.com/rss.xml"],
                x_authors=["openai"],
                x_themes=["ai agents"],
            )
            fake = _FakeProvider()
            with patch("digest.connectors.x_selectors.get_x_provider", return_value=fake):
                items, errors = fetch_x_selector_items(sources, store, provider_mode="x_api")

            self.assertEqual(errors, [])
            self.assertEqual(len(items), 2)
            self.assertTrue(all(item.type == "x_post" for item in items))
            self.assertEqual(store.get_x_cursor("x_author", "openai"), "next-author-cursor")
            self.assertEqual(store.get_x_cursor("x_theme", "ai agents"), "next-theme-cursor")


if __name__ == "__main__":
    unittest.main()
