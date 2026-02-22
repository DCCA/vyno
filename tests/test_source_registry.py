import tempfile
import unittest
from pathlib import Path

from digest.ops.source_registry import add_source, list_sources, load_effective_sources, remove_source


class TestSourceRegistry(unittest.TestCase):
    def test_add_github_org_normalizes_and_dedupes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "sources.yaml"
            overlay = Path(tmp) / "sources.local.yaml"
            base.write_text("rss_feeds: ['https://example.com/rss.xml']\n", encoding="utf-8")

            created, value = add_source(str(base), str(overlay), "github_org", "https://github.com/vercel-labs")
            self.assertTrue(created)
            self.assertEqual(value, "vercel-labs")

            created2, value2 = add_source(str(base), str(overlay), "github_org", "vercel-labs")
            self.assertFalse(created2)
            self.assertEqual(value2, "vercel-labs")

            effective = load_effective_sources(str(base), str(overlay))
            self.assertEqual(effective.github_orgs, ["vercel-labs"])

    def test_remove_masks_base_source_with_tombstone(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "sources.yaml"
            overlay = Path(tmp) / "sources.local.yaml"
            base.write_text(
                "rss_feeds: ['https://example.com/rss.xml', 'https://example.com/2.xml']\n",
                encoding="utf-8",
            )
            removed, value = remove_source(str(base), str(overlay), "rss", "https://example.com/rss.xml")
            self.assertTrue(removed)
            self.assertEqual(value, "https://example.com/rss.xml")

            effective = load_effective_sources(str(base), str(overlay))
            self.assertEqual(effective.rss_feeds, ["https://example.com/2.xml"])

    def test_list_sources_reflects_overlay_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "sources.yaml"
            overlay = Path(tmp) / "sources.local.yaml"
            base.write_text("rss_feeds: ['https://example.com/rss.xml']\n", encoding="utf-8")

            add_source(str(base), str(overlay), "github_repo", "OpenAI/openai-cookbook")
            rows = list_sources(str(base), str(overlay))
            self.assertIn("openai/openai-cookbook", rows["github_repo"])


if __name__ == "__main__":
    unittest.main()
