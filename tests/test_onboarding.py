import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import yaml

from digest.ops.onboarding import (
    OnboardingSettings,
    apply_source_pack,
    build_onboarding_status,
    mark_step_completed,
    run_preflight,
)
from digest.storage.sqlite_store import SQLiteStore


class TestOnboarding(unittest.TestCase):
    def _write_base_files(
        self, tmp: str, *, github: bool = False, safe_profile: bool = False
    ):
        sources = {
            "rss_feeds": ["https://example.com/rss.xml"],
            "youtube_channels": [],
            "youtube_queries": [],
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
        state_path = Path(tmp) / "onboarding-state.json"

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
            history_dir=str(Path(tmp) / "history"),
            onboarding_state_path=str(state_path),
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

    def test_apply_source_pack_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self._write_base_files(tmp, safe_profile=True)

            first = apply_source_pack(settings, "quickstart-core")
            second = apply_source_pack(settings, "quickstart-core")

            self.assertGreater(first["added_count"], 0)
            self.assertEqual(first["error_count"], 0)
            self.assertEqual(second["added_count"], 0)
            self.assertGreater(second["existing_count"], 0)

    def test_onboarding_status_uses_persisted_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self._write_base_files(tmp, safe_profile=True)
            mark_step_completed(
                settings.onboarding_state_path, "preview", details="preview-run"
            )

            store = SQLiteStore(settings.db_path)
            now = datetime.now(timezone.utc).isoformat()
            store.start_run("run123", now, now)
            store.finish_run("run123", "success", [], [])

            status = build_onboarding_status(settings)
            by_id = {row["id"]: row for row in status["steps"]}
            self.assertEqual(by_id["preview"]["status"], "complete")
            self.assertEqual(by_id["activate"]["status"], "complete")
            self.assertGreaterEqual(status["progress"]["completed"], 2)


if __name__ == "__main__":
    unittest.main()
