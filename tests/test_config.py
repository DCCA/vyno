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
            path.write_text(
                "output:\n  telegram_bot_token: ''\n  telegram_chat_id: ''\n",
                encoding="utf-8",
            )
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
                    "github_repo_max_age_days: 21\n"
                    "github_activity_max_age_days: 5\n"
                    "max_agent_items_per_run: 12\n"
                    "quality_repair_enabled: true\n"
                    "quality_repair_model: gpt-5.1-codex-mini\n"
                    "quality_repair_threshold: 80\n"
                    "quality_repair_candidate_pool_size: 40\n"
                    "quality_repair_fail_open: true\n"
                    "quality_learning_enabled: true\n"
                    "quality_learning_max_offset: 7.5\n"
                    "quality_learning_half_life_days: 10\n"
                ),
                encoding="utf-8",
            )
            profile = load_profile(path)
            self.assertEqual(profile.github_min_stars, 100)
            self.assertTrue(profile.github_include_forks)
            self.assertTrue(profile.github_include_archived)
            self.assertEqual(profile.github_max_repos_per_org, 7)
            self.assertEqual(profile.github_max_items_per_org, 11)
            self.assertEqual(profile.github_repo_max_age_days, 21)
            self.assertEqual(profile.github_activity_max_age_days, 5)
            self.assertEqual(profile.max_agent_items_per_run, 12)
            self.assertTrue(profile.quality_repair_enabled)
            self.assertEqual(profile.quality_repair_model, "gpt-5.1-codex-mini")
            self.assertEqual(profile.quality_repair_threshold, 80)
            self.assertEqual(profile.quality_repair_candidate_pool_size, 40)
            self.assertTrue(profile.quality_repair_fail_open)
            self.assertTrue(profile.quality_learning_enabled)
            self.assertEqual(profile.quality_learning_max_offset, 7.5)
            self.assertEqual(profile.quality_learning_half_life_days, 10)

    def test_profile_loads_render_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            path.write_text(
                "output:\n  render_mode: source_segmented\n",
                encoding="utf-8",
            )
            profile = load_profile(path)
            self.assertEqual(profile.output.render_mode, "source_segmented")

    def test_profile_loads_llm_coverage_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            path.write_text(
                (
                    "min_llm_coverage: 0.85\n"
                    "max_fallback_share: 0.15\n"
                    "agent_scoring_retry_attempts: 2\n"
                    "agent_scoring_text_max_chars: 6000\n"
                ),
                encoding="utf-8",
            )
            profile = load_profile(path)
            self.assertEqual(profile.min_llm_coverage, 0.85)
            self.assertEqual(profile.max_fallback_share, 0.15)
            self.assertEqual(profile.agent_scoring_retry_attempts, 2)
            self.assertEqual(profile.agent_scoring_text_max_chars, 6000)

    def test_profile_rejects_invalid_llm_coverage_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            path.write_text("min_llm_coverage: 1.2\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_profile(path)

    def test_profile_rejects_invalid_quality_repair_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            path.write_text("quality_repair_threshold: 120\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_profile(path)


if __name__ == "__main__":
    unittest.main()
