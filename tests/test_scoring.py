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


if __name__ == "__main__":
    unittest.main()
