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
            with (
                patch("digest.connectors.x_selectors.get_x_provider", return_value=fake),
                patch(
                    "digest.connectors.x_selectors.fetch_link_preview_metadata",
                    return_value={
                        "url": "https://example.com/article",
                        "resolved_url": "https://example.com/article",
                        "host": "example.com",
                        "title": "Example AI article",
                        "description": "Deep article from X discovery",
                        "image_url": "",
                        "status": "ready",
                        "error": "",
                    },
                ),
            ):
                items, errors = fetch_x_selector_items(sources, store, provider_mode="x_api")

            self.assertEqual(errors, [])
            self.assertEqual(len(items), 3)
            self.assertEqual([item.type for item in items].count("x_post"), 2)
            self.assertEqual([item.type for item in items].count("link"), 1)
            promoted = next(item for item in items if item.type == "link")
            self.assertEqual(promoted.url, "https://example.com/article")
            self.assertEqual(promoted.source, "example.com")
            self.assertIn("x_endorsed_by:openai", promoted.raw_text)
            self.assertEqual(store.get_x_cursor("x_author", "openai"), "next-author-cursor")
            self.assertEqual(store.get_x_cursor("x_theme", "ai agents"), "next-theme-cursor")

    def test_selector_limits_skip_zero_budget_themes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(str(Path(tmp) / "digest.db"))
            sources = SourceConfig(
                rss_feeds=["https://example.com/rss.xml"],
                x_authors=["openai"],
                x_themes=["ai agents"],
            )
            fake = _FakeProvider()
            with (
                patch("digest.connectors.x_selectors.get_x_provider", return_value=fake),
                patch(
                    "digest.connectors.x_selectors.fetch_link_preview_metadata",
                    return_value={
                        "url": "https://example.com/article",
                        "resolved_url": "https://example.com/article",
                        "host": "example.com",
                        "title": "Example AI article",
                        "description": "Deep article from X discovery",
                        "image_url": "",
                        "status": "ready",
                        "error": "",
                    },
                ),
            ):
                items, errors = fetch_x_selector_items(
                    sources,
                    store,
                    provider_mode="x_api",
                    author_limits={"openai": 3},
                    theme_limits={"ai agents": 0},
                )

            self.assertEqual(errors, [])
            self.assertEqual(fake.author_calls[0][2], 3)
            self.assertEqual(fake.theme_calls, [])
            self.assertEqual([item.type for item in items].count("link"), 1)


if __name__ == "__main__":
    unittest.main()
