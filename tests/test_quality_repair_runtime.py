import json
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from digest.config import OutputSettings, ProfileConfig, SourceConfig
from digest.models import Item
from digest.quality.online_repair import QualityRepairResult
from digest.runtime import run_digest
from digest.storage.sqlite_store import SQLiteStore


def _item(idx: int, *, source: str = "https://regular.example/feed") -> Item:
    return Item(
        id=f"i{idx}",
        url=f"https://example.com/{idx}",
        title=f"Item {idx}",
        source=source,
        author=None,
        published_at=datetime.now(),
        type="article",
        raw_text=("llm agents evals benchmark research " * 40).strip(),
        hash=f"h{idx}",
    )


class _LowQualityRepair:
    def __init__(self, model: str = "x", timeout: int = 30) -> None:
        _ = model, timeout

    def evaluate_and_repair(self, current_must_read, candidate_pool):
        current_ids = [si.item.id for si in current_must_read]
        promoted = candidate_pool[5].item.id
        repaired = [promoted] + [x for x in current_ids if x != promoted][:4]
        return QualityRepairResult(
            quality_score=55.0,
            confidence=0.91,
            issues=["source_monoculture", "redundancy"],
            repaired_must_read_ids=repaired,
            model="x",
        )


class _HighQualityRepair:
    def __init__(self, model: str = "x", timeout: int = 30) -> None:
        _ = model, timeout

    def evaluate_and_repair(self, current_must_read, candidate_pool):
        _ = candidate_pool
        return QualityRepairResult(
            quality_score=91.0,
            confidence=0.88,
            issues=["no_material_issues"],
            repaired_must_read_ids=[si.item.id for si in current_must_read],
            model="x",
        )


class TestQualityRepairRuntime(unittest.TestCase):
    def _profile(self, *, repair_enabled: bool) -> ProfileConfig:
        return ProfileConfig(
            output=OutputSettings(obsidian_vault_path="", obsidian_folder="AI Digest"),
            llm_enabled=False,
            agent_scoring_enabled=False,
            quality_repair_enabled=repair_enabled,
            quality_repair_threshold=80,
            quality_repair_candidate_pool_size=8,
            quality_repair_fail_open=True,
            quality_learning_enabled=True,
            quality_learning_max_offset=8.0,
            quality_learning_half_life_days=14,
        )

    def test_online_repair_applies_below_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db_path))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            items = [_item(i) for i in range(1, 9)]
            items[5].source = "https://special.example/feed"

            captured_must_read: list[list[str]] = []

            def _capture_note(*args, **kwargs):
                sections = args[1]
                captured_must_read.append([si.item.id for si in sections.must_read])
                return "note"

            with (
                patch("digest.runtime.fetch_rss_items", return_value=items),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
                patch("digest.runtime.ResponsesAPIQualityRepair", _LowQualityRepair),
                patch("digest.runtime.render_obsidian_note", side_effect=_capture_note),
            ):
                report = run_digest(
                    sources,
                    self._profile(repair_enabled=True),
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertEqual(report.status, "success")
            self.assertTrue(captured_must_read)
            self.assertEqual(captured_must_read[-1][0], "i6")

            conn = sqlite3.connect(db_path)
            row = conn.execute(
                (
                    "SELECT quality_score, repaired, after_ids_json "
                    "FROM run_quality_eval WHERE run_id = ?"
                ),
                (report.run_id,),
            ).fetchone()
            conn.close()
            self.assertIsNotNone(row)
            self.assertEqual(int(row[1]), 1)
            after_ids = json.loads(str(row[2]))
            self.assertEqual(after_ids[0], "i6")

    def test_online_repair_skips_at_or_above_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db_path))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            items = [_item(i) for i in range(1, 9)]

            captured_must_read: list[list[str]] = []

            def _capture_note(*args, **kwargs):
                sections = args[1]
                captured_must_read.append([si.item.id for si in sections.must_read])
                return "note"

            with (
                patch("digest.runtime.fetch_rss_items", return_value=items),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
                patch("digest.runtime.ResponsesAPIQualityRepair", _HighQualityRepair),
                patch("digest.runtime.render_obsidian_note", side_effect=_capture_note),
            ):
                report = run_digest(
                    sources,
                    self._profile(repair_enabled=True),
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertEqual(report.status, "success")
            self.assertTrue(captured_must_read)
            self.assertEqual(captured_must_read[-1][0], "i1")

            conn = sqlite3.connect(db_path)
            row = conn.execute(
                "SELECT repaired FROM run_quality_eval WHERE run_id = ?",
                (report.run_id,),
            ).fetchone()
            conn.close()
            self.assertIsNotNone(row)
            self.assertEqual(int(row[0]), 0)

    def test_learning_updates_affect_following_run_ranking(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "digest.db"
            store = SQLiteStore(str(db_path))
            sources = SourceConfig(
                rss_feeds=["fixture"], youtube_channels=[], youtube_queries=[]
            )
            items = [_item(i) for i in range(1, 9)]
            items[5].source = "https://special.example/feed"

            captured_must_read: list[list[str]] = []

            def _capture_note(*args, **kwargs):
                sections = args[1]
                captured_must_read.append([si.item.id for si in sections.must_read])
                return "note"

            with (
                patch("digest.runtime.fetch_rss_items", return_value=items),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
                patch("digest.runtime.ResponsesAPIQualityRepair", _LowQualityRepair),
                patch("digest.runtime.render_obsidian_note", side_effect=_capture_note),
            ):
                run_digest(
                    sources,
                    self._profile(repair_enabled=True),
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            second_profile = self._profile(repair_enabled=False)
            with (
                patch("digest.runtime.fetch_rss_items", return_value=items),
                patch("digest.runtime.fetch_youtube_items", return_value=[]),
                patch("digest.runtime.render_obsidian_note", side_effect=_capture_note),
            ):
                run_digest(
                    sources,
                    second_profile,
                    store,
                    use_last_completed_window=False,
                    only_new=False,
                )

            self.assertGreaterEqual(len(captured_must_read), 2)
            self.assertEqual(captured_must_read[-1][0], "i6")


if __name__ == "__main__":
    unittest.main()
