import unittest

from digest.web.app import _web_live_run_options


class TestWebLiveRunOptions(unittest.TestCase):
    def test_web_trigger_uses_incremental_defaults(self):
        options = _web_live_run_options(trigger="web")
        self.assertTrue(options["use_last_completed_window"])
        self.assertTrue(options["only_new"])
        self.assertFalse(options["allow_seen_fallback"])

    def test_non_web_trigger_keeps_broad_defaults(self):
        options = _web_live_run_options(trigger="other")
        self.assertFalse(options["use_last_completed_window"])
        self.assertFalse(options["only_new"])
        self.assertTrue(options["allow_seen_fallback"])


if __name__ == "__main__":
    unittest.main()
