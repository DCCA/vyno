import tempfile
import unittest
from pathlib import Path

from digest.connectors.x_inbox import fetch_x_inbox_items


class TestXInbox(unittest.TestCase):
    def test_parses_valid_x_links_and_skips_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x_inbox.txt"
            p.write_text(
                """
# comment
https://x.com/alice/status/1234567890123456789
invalid line
https://twitter.com/bob/status/9876543210987654321 | interesting thread
""",
                encoding="utf-8",
            )
            items = fetch_x_inbox_items(str(p))
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0].type, "x_post")
            self.assertEqual(items[0].author, "alice")
            self.assertIn("interesting thread", items[1].raw_text)

    def test_normalizes_and_dedupes_urls_and_skips_noise_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x_inbox.txt"
            p.write_text(
                "\n".join(
                    [
                        "https://twitter.com/alice/status/1234567890123456789?ref=share",
                        "https://x.com/alice/status/1234567890123456789",
                        "https://x.com/bob/status/9876543210987654321 | giveaway join now",
                    ]
                ),
                encoding="utf-8",
            )
            items = fetch_x_inbox_items(str(p))
            self.assertEqual(len(items), 1)
            self.assertEqual(
                items[0].url, "https://x.com/alice/status/1234567890123456789"
            )


if __name__ == "__main__":
    unittest.main()
