import unittest
from datetime import datetime

from digest.config import ProfileConfig
from digest.models import Item
from digest.pipeline.scoring import score_item


class TestScoring(unittest.TestCase):
    def test_scoring_respects_keywords(self):
        profile = ProfileConfig(topics=["agents"], entities=["openai"], exclusions=["giveaway"])
        item = Item(
            id="1",
            url="https://example.com/1",
            title="OpenAI agents eval benchmark",
            source="example.com",
            author=None,
            published_at=datetime.now(),
            type="article",
            raw_text="Deep technical eval for llm agents",
        )
        score = score_item(item, profile)
        self.assertGreater(score.total, 0)
        self.assertGreater(score.relevance, 0)
        self.assertEqual(score.provider, "rules")
        self.assertTrue(isinstance(score.tags, list))

    def test_scoring_adds_topic_tags(self):
        profile = ProfileConfig()
        item = Item(
            id="2",
            url="https://example.com/2",
            title="Open source LLM benchmark",
            source="example.com",
            author=None,
            published_at=datetime.now(),
            type="article",
            raw_text="A benchmark paper for LLM agents on GitHub.",
        )
        score = score_item(item, profile)
        self.assertIn("llm", score.topic_tags)
        self.assertIn("benchmark", score.format_tags)
        self.assertLessEqual(len(score.tags), 5)


if __name__ == "__main__":
    unittest.main()
