import unittest

from digest.ops.ingest_detect import detect_ingest


def _no_fetch(url: str) -> tuple[str, str]:
    raise AssertionError(f"unexpected fetch of {url}")


def _page(body: str):
    """Fetch stub: no redirect, returns the requested URL back."""
    return lambda url: (url, body)


class TestDetectIngest(unittest.TestCase):
    def test_github_repo_url(self):
        det = detect_ingest("https://github.com/openai/codex", fetch=_no_fetch)
        self.assertEqual(det.source_type, "github_repo")
        self.assertEqual(det.value, "openai/codex")

    def test_github_org_url(self):
        det = detect_ingest("https://github.com/vercel", fetch=_no_fetch)
        self.assertEqual(det.source_type, "github_org")
        self.assertEqual(det.value, "vercel")

    def test_github_orgs_url_is_org(self):
        det = detect_ingest("https://github.com/orgs/anthropics", fetch=_no_fetch)
        self.assertEqual(det.source_type, "github_org")
        self.assertEqual(det.value, "anthropics")

    def test_github_topics_url_is_topic(self):
        det = detect_ingest("https://github.com/topics/llm", fetch=_no_fetch)
        self.assertEqual(det.source_type, "github_topic")
        self.assertEqual(det.value, "llm")

    def test_github_reserved_path_is_unknown(self):
        det = detect_ingest("https://github.com/features/actions", fetch=_no_fetch)
        self.assertEqual(det.source_type, "")
        self.assertFalse(det.invalid)

    def test_github_malformed_repo_path_is_invalid(self):
        det = detect_ingest("https://github.com/openai/co dex", fetch=_no_fetch)
        self.assertEqual(det.source_type, "")
        self.assertTrue(det.invalid)
        self.assertIn("github_repo", det.note)

    def test_x_profile_url(self):
        det = detect_ingest("https://x.com/karpathy", fetch=_no_fetch)
        self.assertEqual(det.source_type, "x_author")
        self.assertEqual(det.value, "karpathy")

    def test_x_status_url_is_invalid(self):
        det = detect_ingest("https://x.com/i/status/123", fetch=_no_fetch)
        self.assertEqual(det.source_type, "")
        self.assertTrue(det.invalid)
        self.assertIn("x_author", det.note)

    def test_x_author_status_url_is_invalid(self):
        det = detect_ingest("https://x.com/karpathy/status/123", fetch=_no_fetch)
        self.assertEqual(det.source_type, "")
        self.assertTrue(det.invalid)

    def test_x_reserved_path_is_invalid(self):
        det = detect_ingest("https://x.com/home", fetch=_no_fetch)
        self.assertEqual(det.source_type, "")
        self.assertTrue(det.invalid)

    def test_bare_handle(self):
        det = detect_ingest("@Karpathy", fetch=_no_fetch)
        self.assertEqual(det.source_type, "x_author")
        self.assertEqual(det.value, "karpathy")

    def test_invalid_handle_is_invalid(self):
        det = detect_ingest("@not-a-handle!", fetch=_no_fetch)
        self.assertEqual(det.source_type, "")
        self.assertTrue(det.invalid)
        self.assertIn("x_author", det.note)

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
        decoy = "UC" + "d" * 22
        det = detect_ingest(
            "https://www.youtube.com/@someone",
            fetch=_page(
                f"<html><body><p>Sponsored by {decoy}, our friends</p>"
                f'<script>{{"channelId":"{cid}"}}</script></body></html>'
            ),
        )
        self.assertEqual(det.source_type, "youtube_channel")
        self.assertEqual(det.value, cid)

    def test_youtube_channel_id_from_meta_identifier(self):
        cid = "UC" + "e" * 22
        decoy = "UC" + "f" * 22
        det = detect_ingest(
            "https://www.youtube.com/@someone",
            fetch=_page(
                f"<html><head><p>related: {decoy}</p>"
                f'<meta content="{cid}" itemprop="identifier"></head></html>'
            ),
        )
        self.assertEqual(det.source_type, "youtube_channel")
        self.assertEqual(det.value, cid)

    def test_youtube_page_without_channel_id_is_unknown(self):
        det = detect_ingest(
            "https://www.youtube.com/@someone", fetch=_page("<html></html>")
        )
        self.assertEqual(det.source_type, "")

    def test_direct_feed_url(self):
        det = detect_ingest(
            "https://blog.example.com/feed.xml",
            fetch=_page('<?xml version="1.0"?><rss></rss>'),
        )
        self.assertEqual(det.source_type, "rss")
        self.assertEqual(det.value, "https://blog.example.com/feed.xml")

    def test_html_page_with_feed_autodiscovery(self):
        html = (
            "<html><head>"
            '<link rel="alternate" type="application/rss+xml" href="/rss.xml">'
            "</head></html>"
        )
        det = detect_ingest("https://blog.example.com/post", fetch=_page(html))
        self.assertEqual(det.source_type, "rss")
        self.assertEqual(det.value, "https://blog.example.com/rss.xml")

    def test_feed_autodiscovery_ignores_attribute_order(self):
        html = (
            "<html><head>"
            "<link href='/atom.xml' type='APPLICATION/ATOM+XML' rel='alternate'>"
            "</head></html>"
        )
        det = detect_ingest("https://blog.example.com/post", fetch=_page(html))
        self.assertEqual(det.source_type, "rss")
        self.assertEqual(det.value, "https://blog.example.com/atom.xml")

    def test_feed_href_resolves_against_redirect_target(self):
        html = (
            "<html><head>"
            '<link rel="alternate" type="application/rss+xml" href="feed.xml">'
            "</head></html>"
        )
        det = detect_ingest(
            "https://example.com/blog",
            fetch=lambda url: ("https://blog.example.com/index.html", html),
        )
        self.assertEqual(det.source_type, "rss")
        self.assertEqual(det.value, "https://blog.example.com/feed.xml")

    def test_html_page_without_feed_is_unknown(self):
        det = detect_ingest(
            "https://app.example.com/dash", fetch=_page("<html>no feeds</html>")
        )
        self.assertEqual(det.source_type, "")
        self.assertEqual(det.value, "https://app.example.com/dash")

    def test_unreachable_url_is_unknown_with_note(self):
        def boom(url: str) -> tuple[str, str]:
            raise OSError("connection refused")

        det = detect_ingest("https://down.example.com/", fetch=boom)
        self.assertEqual(det.source_type, "")
        self.assertEqual(det.note, "unreachable")
        self.assertFalse(det.invalid)

    def test_plain_text_is_none(self):
        self.assertIsNone(detect_ingest("hello world", fetch=_no_fetch))


if __name__ == "__main__":
    unittest.main()
