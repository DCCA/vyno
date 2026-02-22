import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from digest.config import load_profile, load_sources


class TestConfig(unittest.TestCase):
    def test_sources_require_at_least_one_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.yaml"
            path.write_text("rss_feeds: []\nyoutube_channels: []\nyoutube_queries: []\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_sources(path)

    def test_profile_rejects_invalid_obsidian_naming(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            path.write_text(
                "output:\n  obsidian_naming: invalid\n",
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


if __name__ == "__main__":
    unittest.main()
