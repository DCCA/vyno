import unittest

from digest.ops.ingest_detect import detect_ingest


def _no_fetch(url: str) -> str:
    raise AssertionError(f"unexpected fetch of {url}")


class TestDetectIngest(unittest.TestCase):
    def test_github_repo_url(self):
        det = detect_ingest("https://github.com/openai/codex", fetch=_no_fetch)
        self.assertEqual(det.source_type, "github_repo")
        self.assertEqual(det.value, "openai/codex")

    def test_github_org_url(self):
        det = detect_ingest("https://github.com/vercel", fetch=_no_fetch)
        self.assertEqual(det.source_type, "github_org")
        self.assertEqual(det.value, "vercel")

    def test_x_profile_url(self):
        det = detect_ingest("https://x.com/karpathy", fetch=_no_fetch)
        self.assertEqual(det.source_type, "x_author")
        self.assertEqual(det.value, "karpathy")

    def test_bare_handle(self):
        det = detect_ingest("@Karpathy", fetch=_no_fetch)
        self.assertEqual(det.source_type, "x_author")
        self.assertEqual(det.value, "karpathy")

    def test_bare_youtube_channel_id(self):
        cid = "UC" + "a" * 22
        det = detect_ingest(cid, fetch=_no_fetch)
        self.assertEqual(det.source_type, "youtube_channel")
        self.assertEqual(det.value, cid)

    def test_youtube_channel_url(self):
        cid = "UC" + "b" * 22
        det = detect_ingest(f"https://www.youtube.com/channel/{cid}", fetch=_no_fetch)
        self.assertEqual(det.source_type, "youtube_channel")
        self.assertEqual(det.value, cid)

    def test_youtube_handle_url_resolves_channel_id_from_page(self):
        cid = "UC" + "c" * 22
        det = detect_ingest(
            "https://www.youtube.com/@someone",
            fetch=lambda url: f'<html>"channelId":"{cid}"</html>',
        )
        self.assertEqual(det.source_type, "youtube_channel")
        self.assertEqual(det.value, cid)

    def test_youtube_page_without_channel_id_is_unknown(self):
        det = detect_ingest(
            "https://www.youtube.com/@someone", fetch=lambda url: "<html></html>"
        )
        self.assertEqual(det.source_type, "")

    def test_direct_feed_url(self):
        det = detect_ingest(
            "https://blog.example.com/feed.xml",
            fetch=lambda url: '<?xml version="1.0"?><rss></rss>',
        )
        self.assertEqual(det.source_type, "rss")
        self.assertEqual(det.value, "https://blog.example.com/feed.xml")

    def test_html_page_with_feed_autodiscovery(self):
        html = (
            "<html><head>"
            '<link rel="alternate" type="application/rss+xml" href="/rss.xml">'
            "</head></html>"
        )
        det = detect_ingest("https://blog.example.com/post", fetch=lambda url: html)
        self.assertEqual(det.source_type, "rss")
        self.assertEqual(det.value, "https://blog.example.com/rss.xml")

    def test_html_page_without_feed_is_unknown(self):
        det = detect_ingest(
            "https://app.example.com/dash", fetch=lambda url: "<html>no feeds</html>"
        )
        self.assertEqual(det.source_type, "")
        self.assertEqual(det.value, "https://app.example.com/dash")

    def test_unreachable_url_is_unknown_with_note(self):
        def boom(url: str) -> str:
            raise OSError("connection refused")

        det = detect_ingest("https://down.example.com/", fetch=boom)
        self.assertEqual(det.source_type, "")
        self.assertIn("unreachable", det.note)

    def test_plain_text_is_none(self):
        self.assertIsNone(detect_ingest("hello world", fetch=_no_fetch))


if __name__ == "__main__":
    unittest.main()
