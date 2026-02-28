import tempfile
import unittest
from pathlib import Path

import yaml

from digest.ops.profile_registry import (
    load_effective_profile,
    load_effective_profile_dict,
    save_profile_overlay,
)


class TestProfileRegistry(unittest.TestCase):
    def test_load_effective_profile_merges_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "profile.yaml"
            overlay = Path(tmp) / "profile.local.yaml"
            base.write_text(
                (
                    "llm_enabled: false\n"
                    "max_agent_items_per_run: 40\n"
                    "output:\n"
                    "  obsidian_folder: AI Digest\n"
                ),
                encoding="utf-8",
            )
            overlay.write_text(
                ("llm_enabled: true\noutput:\n  obsidian_folder: My Digest\n"),
                encoding="utf-8",
            )

            merged = load_effective_profile_dict(str(base), str(overlay))
            self.assertTrue(merged["llm_enabled"])
            self.assertEqual(merged["max_agent_items_per_run"], 40)
            self.assertEqual(merged["output"]["obsidian_folder"], "My Digest")

            profile = load_effective_profile(str(base), str(overlay))
            self.assertTrue(profile.llm_enabled)
            self.assertEqual(profile.output.obsidian_folder, "My Digest")

    def test_save_profile_overlay_writes_changed_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "profile.yaml"
            overlay = Path(tmp) / "profile.local.yaml"
            base.write_text(
                (
                    "llm_enabled: false\n"
                    "max_agent_items_per_run: 40\n"
                    "output:\n"
                    "  obsidian_folder: AI Digest\n"
                    "  render_mode: sectioned\n"
                ),
                encoding="utf-8",
            )

            payload = {
                "llm_enabled": True,
                "max_agent_items_per_run": 40,
                "output": {
                    "obsidian_folder": "AI Digest",
                    "render_mode": "source_segmented",
                },
            }

            saved_overlay = save_profile_overlay(str(base), str(overlay), payload)
            self.assertTrue(saved_overlay["llm_enabled"])
            self.assertEqual(saved_overlay["output"]["render_mode"], "source_segmented")
            self.assertNotIn("max_agent_items_per_run", saved_overlay)

            persisted = yaml.safe_load(overlay.read_text(encoding="utf-8"))
            self.assertEqual(persisted, saved_overlay)


if __name__ == "__main__":
    unittest.main()
