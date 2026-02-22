import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from digest.models import Item
from digest.runtime import _filter_window
from digest.storage.sqlite_store import SQLiteStore


class TestRuntimeWindow(unittest.TestCase):
    def test_filter_window_drops_old_items(self):
        start = datetime.now(timezone.utc) - timedelta(hours=24)
        old_item = Item("1", "https://x/1", "old", "src", None, start - timedelta(minutes=1), "article", "text")
        new_item = Item("2", "https://x/2", "new", "src", None, start + timedelta(minutes=1), "article", "text")
        unknown_item = Item("3", "https://x/3", "unknown", "src", None, None, "article", "text")
        out = _filter_window([old_item, new_item, unknown_item], start.isoformat())
        self.assertEqual([i.id for i in out], ["2", "3"])

    def test_store_returns_last_completed_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db))
            store.start_run("r1", "2026-02-20T00:00:00+00:00", "2026-02-21T00:00:00+00:00")
            store.finish_run("r1", "success", [], [])
            self.assertEqual(store.last_completed_window_end(), "2026-02-21T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
