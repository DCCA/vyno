import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from digest.ops.onboarding import OnboardingSettings, run_preflight


class TestOnboarding(unittest.TestCase):
    def _write_base_files(
        self, tmp: str, *, github: bool = False, safe_profile: bool = False
    ):
        sources = {
            "rss_feeds": ["https://example.com/rss.xml"],
            "youtube_channels": [],
            "github_repos": ["openai/openai-cookbook"] if github else [],
            "github_topics": [],
            "github_search_queries": [],
            "github_orgs": [],
            "x_inbox_path": "",
        }
        profile = {
            "output": {
                "telegram_bot_token": "",
                "telegram_chat_id": "",
                "obsidian_vault_path": "",
                "obsidian_folder": "AI Digest",
            }
        }
        if safe_profile:
            profile.update(
                {
                    "agent_scoring_enabled": False,
                    "llm_enabled": False,
                    "quality_repair_enabled": False,
                }
            )

        base_sources = Path(tmp) / "sources.yaml"
        overlay_sources = Path(tmp) / "sources.local.yaml"
        base_profile = Path(tmp) / "profile.yaml"
        overlay_profile = Path(tmp) / "profile.local.yaml"
        db_path = Path(tmp) / "digest.db"

        base_sources.write_text(
            yaml.safe_dump(sources, sort_keys=False), encoding="utf-8"
        )
        overlay_sources.write_text("{}\n", encoding="utf-8")
        base_profile.write_text(
            yaml.safe_dump(profile, sort_keys=False), encoding="utf-8"
        )
        overlay_profile.write_text("{}\n", encoding="utf-8")

        return OnboardingSettings(
            sources_path=str(base_sources),
            sources_overlay_path=str(overlay_sources),
            profile_path=str(base_profile),
            profile_overlay_path=str(overlay_profile),
            db_path=str(db_path),
            run_lock_path=str(Path(tmp) / "run.lock"),
        )

    def test_preflight_fails_when_openai_key_missing_for_enabled_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self._write_base_files(tmp, safe_profile=False)
            with patch.dict(
                "os.environ", {"OPENAI_API_KEY": "", "GITHUB_TOKEN": ""}, clear=False
            ):
                report = run_preflight(settings, check_network=False)

            checks = {c["id"]: c for c in report["checks"]}
            self.assertEqual(checks["openai_key"]["status"], "fail")
            self.assertFalse(report["ok"])

    def test_preflight_warns_when_github_token_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self._write_base_files(tmp, github=True, safe_profile=True)
            with patch.dict(
                "os.environ", {"OPENAI_API_KEY": "", "GITHUB_TOKEN": ""}, clear=False
            ):
                report = run_preflight(settings, check_network=False)

            checks = {c["id"]: c for c in report["checks"]}
            self.assertEqual(checks["github_token"]["status"], "warn")
            self.assertTrue(report["ok"])
            # config-history died with the web console - no check for it.
            self.assertNotIn("history_writable", checks)


if __name__ == "__main__":
    unittest.main()
