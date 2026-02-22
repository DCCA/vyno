import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from digest.config import load_profile, load_sources


class TestConfig(unittest.TestCase):
    def test_sources_require_at_least_one_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.yaml"
            path.write_text(
                "rss_feeds: []\nyoutube_channels: []\nyoutube_queries: []\ngithub_repos: []\ngithub_topics: []\ngithub_search_queries: []\ngithub_orgs: []\nx_inbox_path: ''\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_sources(path)

    def test_sources_loads_x_and_github_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.yaml"
            path.write_text(
                "x_inbox_path: data/x.txt\ngithub_repos: ['openai/openai-cookbook']\ngithub_topics: ['llm']\ngithub_search_queries: ['is:issue llm']\n",
                encoding="utf-8",
            )
            cfg = load_sources(path)
            self.assertEqual(cfg.x_inbox_path, "data/x.txt")
            self.assertIn("openai/openai-cookbook", cfg.github_repos)

    def test_sources_loads_github_orgs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.yaml"
            path.write_text(
                "github_orgs: ['https://github.com/vercel-labs', 'openai']\n",
                encoding="utf-8",
            )
            cfg = load_sources(path)
            self.assertEqual(cfg.github_orgs, ["vercel-labs", "openai"])

    def test_profile_rejects_invalid_obsidian_naming(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            path.write_text(
                "output:\n  obsidian_naming: invalid\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_profile(path)

    def test_profile_rejects_invalid_render_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            path.write_text(
                "output:\n  render_mode: invalid\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_profile(path)

    def test_profile_uses_env_fallback_for_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            path.write_text("output:\n  telegram_bot_token: ''\n  telegram_chat_id: ''\n", encoding="utf-8")
            with patch.dict(
                "os.environ",
                {
                    "TELEGRAM_BOT_TOKEN": "token123",
                    "TELEGRAM_CHAT_ID": "chat123",
                },
                clear=False,
            ):
                profile = load_profile(path)
            self.assertEqual(profile.output.telegram_bot_token, "token123")
            self.assertEqual(profile.output.telegram_chat_id, "chat123")

    def test_profile_loads_github_guardrails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            path.write_text(
                (
                    "github_min_stars: 100\n"
                    "github_include_forks: true\n"
                    "github_include_archived: true\n"
                    "github_max_repos_per_org: 7\n"
                    "github_max_items_per_org: 11\n"
                ),
                encoding="utf-8",
            )
            profile = load_profile(path)
            self.assertEqual(profile.github_min_stars, 100)
            self.assertTrue(profile.github_include_forks)
            self.assertTrue(profile.github_include_archived)
            self.assertEqual(profile.github_max_repos_per_org, 7)
            self.assertEqual(profile.github_max_items_per_org, 11)

    def test_profile_loads_render_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            path.write_text(
                "output:\n  render_mode: source_segmented\n",
                encoding="utf-8",
            )
            profile = load_profile(path)
            self.assertEqual(profile.output.render_mode, "source_segmented")


if __name__ == "__main__":
    unittest.main()
