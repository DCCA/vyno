import unittest

from digest.web.app import _parse_source_error


class TestWebSourceHealth(unittest.TestCase):
    def test_parse_github_403_error_has_actionable_hint(self):
        parsed = _parse_source_error(
            "github: GitHub API HTTPError: 403 (/repos/openai/openai-cookbook/releases?per_page=5)"
        )
        self.assertEqual(parsed["kind"], "github")
        self.assertIn("/repos/openai/openai-cookbook/releases", parsed["source"])
        self.assertIn("GITHUB_TOKEN", parsed["hint"])

    def test_parse_rss_error_extracts_feed_url(self):
        parsed = _parse_source_error("rss:https://news.ycombinator.com/rss: timed out")
        self.assertEqual(parsed["kind"], "rss")
        self.assertEqual(parsed["source"], "https://news.ycombinator.com/rss")
        self.assertIn("Feed", parsed["hint"])


if __name__ == "__main__":
    unittest.main()
