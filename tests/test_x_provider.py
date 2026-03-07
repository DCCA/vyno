import json
import unittest
import urllib.parse
from unittest.mock import MagicMock, patch

from digest.connectors.x_provider import XApiProvider


def _response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    context = MagicMock()
    context.__enter__.return_value = response
    context.__exit__.return_value = False
    return context


class TestXApiProvider(unittest.TestCase):
    def test_author_posts_use_recent_search_query(self):
        provider = XApiProvider(bearer_token="test-token", timeout=5)
        payload = {
            "data": [
                {
                    "id": "111",
                    "text": "Author update",
                    "author_id": "u1",
                    "created_at": "2026-03-01T00:00:00Z",
                }
            ],
            "includes": {"users": [{"id": "u1", "username": "openai"}]},
            "meta": {"next_token": "next-author"},
        }

        with patch(
            "digest.connectors.x_provider.urllib.request.urlopen",
            return_value=_response(payload),
        ) as urlopen:
            posts, cursor = provider.fetch_author_posts(
                author="@OpenAI",
                cursor="cursor-1",
                limit=25,
            )

        self.assertEqual(cursor, "next-author")
        self.assertEqual(posts[0].author_username, "openai")
        self.assertEqual(posts[0].url, "https://x.com/openai/status/111")

        request = urlopen.call_args.args[0]
        parsed = urllib.parse.urlparse(request.full_url)
        params = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(parsed.path, "/2/tweets/search/recent")
        self.assertEqual(params["query"], ["from:openai -is:retweet -is:reply"])
        self.assertEqual(params["next_token"], ["cursor-1"])
        self.assertEqual(params["sort_order"], ["recency"])

    def test_theme_posts_pass_query_through_recent_search(self):
        provider = XApiProvider(bearer_token="test-token", timeout=5)
        payload = {
            "data": [
                {
                    "id": "222",
                    "text": "Theme update",
                    "author_id": "u2",
                    "created_at": "2026-03-01T00:00:00Z",
                }
            ],
            "includes": {"users": [{"id": "u2", "username": "newsbot"}]},
            "meta": {"next_token": "next-theme"},
        }

        with patch(
            "digest.connectors.x_provider.urllib.request.urlopen",
            return_value=_response(payload),
        ) as urlopen:
            posts, cursor = provider.fetch_theme_posts(
                query="ai agents lang:en",
                cursor=None,
                limit=10,
            )

        self.assertEqual(cursor, "next-theme")
        self.assertEqual(posts[0].author_username, "newsbot")

        request = urlopen.call_args.args[0]
        parsed = urllib.parse.urlparse(request.full_url)
        params = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(parsed.path, "/2/tweets/search/recent")
        self.assertEqual(params["query"], ["ai agents lang:en"])
        self.assertNotIn("next_token", params)


if __name__ == "__main__":
    unittest.main()
