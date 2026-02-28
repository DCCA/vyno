import json
import os
import unittest
import urllib.error
from datetime import datetime
from unittest.mock import patch

from digest.models import Item
from digest.summarizers.responses_api import ResponsesAPISummarizer


class _FakeHTTPResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


class TestResponsesAPISummarizer(unittest.TestCase):
    def _item(self) -> Item:
        return Item(
            id="item-1",
            url="https://example.com/item",
            title="Example Item",
            source="example.com",
            author=None,
            published_at=datetime.now(),
            type="article",
            raw_text="Example body text for summarizer.",
        )

    def _success_payload(self) -> dict:
        return {
            "output": [
                {
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(
                                {
                                    "tldr": "Short summary",
                                    "key_points": ["one", "two"],
                                    "why_it_matters": "Because it helps",
                                }
                            ),
                        }
                    ]
                }
            ]
        }

    def test_retries_on_http_500_then_succeeds(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            summarizer = ResponsesAPISummarizer(
                model="gpt-5.1-codex-mini",
                timeout=1,
                retries=1,
                retry_backoff_seconds=0,
            )

        err_500 = urllib.error.HTTPError(
            url="https://api.openai.com/v1/responses",
            code=500,
            msg="Server Error",
            hdrs=None,
            fp=None,
        )

        with patch(
            "urllib.request.urlopen",
            side_effect=[err_500, _FakeHTTPResponse(self._success_payload())],
        ) as mock_urlopen:
            summary = summarizer.summarize(self._item())

        self.assertEqual(summary.provider, "openai_responses")
        self.assertEqual(summary.tldr, "Short summary")
        self.assertEqual(mock_urlopen.call_count, 2)

    def test_does_not_retry_on_http_400(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            summarizer = ResponsesAPISummarizer(
                model="gpt-5.1-codex-mini",
                timeout=1,
                retries=3,
                retry_backoff_seconds=0,
            )

        err_400 = urllib.error.HTTPError(
            url="https://api.openai.com/v1/responses",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=None,
        )

        with patch("urllib.request.urlopen", side_effect=[err_400]) as mock_urlopen:
            with self.assertRaises(RuntimeError) as cm:
                summarizer.summarize(self._item())

        self.assertIn("HTTPError: 400", str(cm.exception))
        self.assertEqual(mock_urlopen.call_count, 1)

    def test_retries_on_timeout_then_succeeds(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            summarizer = ResponsesAPISummarizer(
                model="gpt-5.1-codex-mini",
                timeout=1,
                retries=1,
                retry_backoff_seconds=0,
            )

        with patch(
            "urllib.request.urlopen",
            side_effect=[
                TimeoutError("timed out"),
                _FakeHTTPResponse(self._success_payload()),
            ],
        ) as mock_urlopen:
            summary = summarizer.summarize(self._item())

        self.assertEqual(summary.provider, "openai_responses")
        self.assertEqual(mock_urlopen.call_count, 2)


if __name__ == "__main__":
    unittest.main()
