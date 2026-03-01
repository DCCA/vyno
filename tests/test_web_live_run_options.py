import unittest
from types import SimpleNamespace

from digest.web.app import _resolve_run_mode_for_request, _web_live_run_options


class TestWebLiveRunOptions(unittest.TestCase):
    def test_web_trigger_uses_incremental_defaults(self):
        options = _web_live_run_options(trigger="web")
        self.assertTrue(options["use_last_completed_window"])
        self.assertTrue(options["only_new"])
        self.assertFalse(options["allow_seen_fallback"])

    def test_web_trigger_can_use_balanced_mode(self):
        options = _web_live_run_options(trigger="web", mode="balanced")
        self.assertTrue(options["use_last_completed_window"])
        self.assertTrue(options["only_new"])
        self.assertTrue(options["allow_seen_fallback"])

    def test_non_web_trigger_keeps_broad_defaults(self):
        options = _web_live_run_options(trigger="other")
        self.assertFalse(options["use_last_completed_window"])
        self.assertFalse(options["only_new"])
        self.assertTrue(options["allow_seen_fallback"])

    def test_run_mode_override_respects_profile_guard(self):
        profile = SimpleNamespace(
            run_policy=SimpleNamespace(
                default_mode="fresh_only", allow_run_override=False
            )
        )
        mode = _resolve_run_mode_for_request(
            profile_cfg=profile, requested_mode="backfill"
        )
        self.assertEqual(mode, "fresh_only")


if __name__ == "__main__":
    unittest.main()
