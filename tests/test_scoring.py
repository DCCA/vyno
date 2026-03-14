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

    def test_scoring_boosts_x_endorsed_links(self):
        profile = ProfileConfig()
        plain = Item(
            id="3",
            url="https://example.com/plain",
            title="Useful AI article",
            source="example.com",
            author=None,
            published_at=datetime.now(),
            type="link",
            raw_text="Useful AI article body",
        )
        endorsed = Item(
            id="4",
            url="https://example.com/endorsed",
            title="Useful AI article",
            source="example.com",
            author=None,
            published_at=datetime.now(),
            type="link",
            raw_text="Useful AI article body | x_endorsed_by:openai | x_endorsed_by:sama",
        )
        plain_score = score_item(plain, profile)
        endorsed_score = score_item(endorsed, profile)
        self.assertGreater(endorsed_score.quality, plain_score.quality)
        self.assertIn("x-discovered", endorsed_score.format_tags)


if __name__ == "__main__":
    unittest.main()
