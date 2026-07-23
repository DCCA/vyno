import os
import unittest
from datetime import datetime
from unittest.mock import patch

from digest.models import Item
from digest.summarizers.responses_api import ResponsesAPISummarizer


class _FakeClient:
    """Stands in for a LangChain structured-output runnable."""

    def __init__(self, result=None, error: Exception | None = None):
        self._result = result
        self._error = error
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._result


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

    def test_success_returns_expected_summary_shape(self):
        client = _FakeClient(
            result={
                "tldr": "Short summary",
                "key_points": ["one", "two"],
                "why_it_matters": "Because it helps",
            }
        )
        summarizer = ResponsesAPISummarizer(model="gpt-5.1-codex-mini", client=client)
        summary = summarizer.summarize(self._item())

        self.assertEqual(summary.provider, "openai_responses")
        self.assertEqual(summary.tldr, "Short summary")
        self.assertEqual(summary.key_points, ["one", "two"])
        self.assertEqual(summary.why_it_matters, "Because it helps")
        self.assertEqual(client.calls, 1)

    def test_client_error_raises_runtime_error(self):
        client = _FakeClient(error=ValueError("upstream 500"))
        summarizer = ResponsesAPISummarizer(model="gpt-5.1-codex-mini", client=client)
        with self.assertRaises(RuntimeError) as cm:
            summarizer.summarize(self._item())
        self.assertIn("upstream 500", str(cm.exception))

    def test_retries_map_to_model_max_retries(self):
        captured = {}

        def _fake_structured_model(*, model, schema, timeout, max_retries):
            captured["max_retries"] = max_retries
            return _FakeClient(result={"tldr": "x", "key_points": [], "why_it_matters": "y"})

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            with patch(
                "digest.summarizers.responses_api.structured_model",
                side_effect=_fake_structured_model,
            ):
                ResponsesAPISummarizer(model="gpt-5.1-codex-mini", retries=3)

        self.assertEqual(captured["max_retries"], 3)

    def test_missing_api_key_raises_for_fallback(self):
        # No OPENAI_API_KEY (and no injected client) -> RuntimeError, so the
        # runtime falls back to the extractive summarizer.
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            with self.assertRaises(RuntimeError):
                ResponsesAPISummarizer(model="gpt-5.1-codex-mini")


if __name__ == "__main__":
    unittest.main()
