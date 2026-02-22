import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from digest.config import OutputSettings, ProfileConfig, SourceConfig
from digest.logging_utils import get_run_logger, log_event, setup_logging
from digest.models import Item
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore


class TestLogging(unittest.TestCase):
    def test_json_log_line_written(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            "os.environ",
            {
                "DIGEST_LOG_PATH": str(Path(tmp) / "digest.log"),
                "DIGEST_LOG_LEVEL": "INFO",
            },
            clear=False,
        ):
            setup_logging(force=True)
            logger = get_run_logger("run123")
            log_event(logger, "info", "test_stage", "hello", foo="bar")

            raw = (Path(tmp) / "digest.log").read_text(encoding="utf-8").strip().splitlines()[-1]
            row = json.loads(raw)
            self.assertEqual(row["run_id"], "run123")
            self.assertEqual(row["stage"], "test_stage")
            self.assertEqual(row["message"], "hello")
            self.assertEqual(row["foo"], "bar")

    def test_run_emits_start_and_finish_events(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            "os.environ",
            {
                "DIGEST_LOG_PATH": str(Path(tmp) / "digest.log"),
                "DIGEST_LOG_LEVEL": "INFO",
            },
            clear=False,
        ):
            setup_logging(force=True)
            db = Path(tmp) / "digest.db"
            vault = Path(tmp) / "vault"
            store = SQLiteStore(str(db))
            sources = SourceConfig(rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[])
            profile = ProfileConfig(
                output=OutputSettings(obsidian_vault_path=str(vault), obsidian_folder="AI Digest"),
                llm_enabled=False,
            )

            fixture_item = Item(
                id="fixture1",
                url="https://example.com/fixture1",
                title="OpenAI evals update",
                source="fixture-source",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="Detailed ai evals coverage.",
                hash="fixturehash1",
            )

            with patch("digest.runtime.fetch_rss_items", return_value=[fixture_item]), patch(
                "digest.runtime.fetch_youtube_items", return_value=[]
            ):
                report = run_digest(sources, profile, store, use_last_completed_window=False, only_new=False)

            lines = (Path(tmp) / "digest.log").read_text(encoding="utf-8").splitlines()
            rows = [json.loads(line) for line in lines if line.strip()]
            run_rows = [r for r in rows if r.get("run_id") == report.run_id]
            stages = {r.get("stage") for r in run_rows}
            self.assertIn("run_start", stages)
            self.assertIn("run_finish", stages)


if __name__ == "__main__":
    unittest.main()
