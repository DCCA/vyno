import unittest
from unittest.mock import patch

from digest.web.app import (
    REDACTED_SECRET,
    _api_auth_decision,
    _redact_secrets,
    _rehydrate_redacted_value,
    _web_api_auth_mode,
)


class TestWebSecurityHelpers(unittest.TestCase):
    def test_auth_decision_bypasses_health_and_preflight(self):
        allowed, status_code, _ = _api_auth_decision(
            path="/api/health",
            method="GET",
            mode="required",
            configured_token="secret",
            presented_token="",
        )
        self.assertTrue(allowed)
        self.assertEqual(status_code, 200)

        allowed, status_code, _ = _api_auth_decision(
            path="/api/run-status",
            method="OPTIONS",
            mode="required",
            configured_token="secret",
            presented_token="",
        )
        self.assertTrue(allowed)
        self.assertEqual(status_code, 200)

    def test_auth_decision_required_mode(self):
        allowed, status_code, detail = _api_auth_decision(
            path="/api/config/profile",
            method="GET",
            mode="required",
            configured_token="",
            presented_token="",
        )
        self.assertFalse(allowed)
        self.assertEqual(status_code, 503)
        self.assertIn("DIGEST_WEB_API_TOKEN", detail)

        allowed, status_code, detail = _api_auth_decision(
            path="/api/config/profile",
            method="GET",
            mode="required",
            configured_token="secret",
            presented_token="bad",
        )
        self.assertFalse(allowed)
        self.assertEqual(status_code, 401)
        self.assertIn("invalid", detail)

        allowed, status_code, _ = _api_auth_decision(
            path="/api/config/profile",
            method="GET",
            mode="required",
            configured_token="secret",
            presented_token="secret",
        )
        self.assertTrue(allowed)
        self.assertEqual(status_code, 200)

    def test_auth_decision_optional_mode(self):
        allowed, status_code, _ = _api_auth_decision(
            path="/api/config/profile",
            method="GET",
            mode="optional",
            configured_token="",
            presented_token="",
        )
        self.assertTrue(allowed)
        self.assertEqual(status_code, 200)

        allowed, status_code, _ = _api_auth_decision(
            path="/api/config/profile",
            method="GET",
            mode="optional",
            configured_token="secret",
            presented_token="secret",
        )
        self.assertTrue(allowed)
        self.assertEqual(status_code, 200)

    def test_auth_mode_env_parsing(self):
        with patch.dict("os.environ", {"DIGEST_WEB_API_AUTH_MODE": "off"}, clear=False):
            self.assertEqual(_web_api_auth_mode(), "off")

        with patch.dict(
            "os.environ", {"DIGEST_WEB_API_AUTH_MODE": "nonsense"}, clear=False
        ):
            self.assertEqual(_web_api_auth_mode(), "required")

    def test_redact_and_rehydrate_secrets(self):
        current = {
            "llm_enabled": True,
            "output": {
                "telegram_bot_token": "abc123",
                "telegram_chat_id": "999",
                "obsidian_folder": "AI Digest",
            },
            "api_key": "test-key",
        }
        redacted = _redact_secrets(current)
        self.assertEqual(redacted["output"]["telegram_bot_token"], REDACTED_SECRET)
        self.assertEqual(redacted["api_key"], REDACTED_SECRET)
        self.assertEqual(redacted["output"]["obsidian_folder"], "AI Digest")

        candidate = {
            "llm_enabled": False,
            "output": {
                "telegram_bot_token": REDACTED_SECRET,
                "telegram_chat_id": REDACTED_SECRET,
                "obsidian_folder": "New Folder",
            },
            "api_key": REDACTED_SECRET,
        }
        hydrated = _rehydrate_redacted_value(candidate, current)
        self.assertEqual(hydrated["output"]["telegram_bot_token"], "abc123")
        self.assertEqual(hydrated["output"]["telegram_chat_id"], "999")
        self.assertEqual(hydrated["api_key"], "test-key")
        self.assertEqual(hydrated["llm_enabled"], False)
        self.assertEqual(hydrated["output"]["obsidian_folder"], "New Folder")


if __name__ == "__main__":
    unittest.main()
