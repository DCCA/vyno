import unittest
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from unittest.mock import patch

from digest.delivery.obsidian import build_obsidian_note_path, write_obsidian_note


class TestObsidianPaths(unittest.TestCase):
    def test_timestamped_path_contains_day_folder_and_run_id(self):
        dt = datetime(2026, 2, 22, 13, 45, 10, tzinfo=timezone.utc)
        path = build_obsidian_note_path("/vault", "AI Digest", "timestamped", dt, "a1b2c3d4e5f6")
        self.assertEqual(str(path), "/vault/AI Digest/2026-02-22/134510-a1b2c3d4e5f6.md")

    def test_midnight_boundary_uses_different_day_folders(self):
        one = datetime(2026, 2, 22, 23, 59, 59, tzinfo=timezone.utc)
        two = datetime(2026, 2, 23, 0, 0, 1, tzinfo=timezone.utc)
        p1 = build_obsidian_note_path("/vault", "AI Digest", "timestamped", one, "run1")
        p2 = build_obsidian_note_path("/vault", "AI Digest", "timestamped", two, "run2")
        self.assertIn("/2026-02-22/", str(p1))
        self.assertIn("/2026-02-23/", str(p2))

    def test_daily_mode_keeps_legacy_filename(self):
        dt = datetime(2026, 2, 22, 13, 45, 10, tzinfo=timezone.utc)
        path = build_obsidian_note_path("/vault", "AI Digest", "daily", dt, "a1")
        self.assertEqual(str(path), "/vault/AI Digest/2026-02-22.md")

    def test_build_path_expands_home_directory(self):
        dt = datetime(2026, 2, 22, 13, 45, 10, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"HOME": tmp}, clear=False):
                path = build_obsidian_note_path("~/vault", "AI Digest", "daily", dt, "a1")
        self.assertEqual(str(path), str(Path(tmp) / "vault" / "AI Digest" / "2026-02-22.md"))

    def test_write_obsidian_note_uses_expanded_home_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"HOME": tmp}, clear=False):
                out_path = write_obsidian_note(
                    "~/vault",
                    "AI Digest",
                    "2026-02-22",
                    "# Test\n",
                    naming="daily",
                    run_id="run1",
                    run_dt_utc=datetime(2026, 2, 22, 13, 45, 10, tzinfo=timezone.utc),
                )
                expected = Path(tmp) / "vault" / "AI Digest" / "2026-02-22.md"
                self.assertEqual(out_path, expected)
                self.assertTrue(expected.exists())


if __name__ == "__main__":
    unittest.main()
