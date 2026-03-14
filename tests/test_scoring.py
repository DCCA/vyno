import unittest
from datetime import datetime

from digest.config import ProfileConfig
from digest.models import Item, Score, ScoredItem
from digest.pipeline.scoring import (
    research_concentration_adjustments,
    score_item,
    source_preference_adjustment,
)


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

    def test_trusted_sources_do_not_inflate_raw_score(self):
        trusted_profile = ProfileConfig(trusted_sources=["example.com"])
        plain_profile = ProfileConfig()
        item = Item(
            id="trust-1",
            url="https://example.com/post",
            title="AI product launch",
            source="https://example.com/feed.xml",
            author=None,
            published_at=datetime.now(),
            type="article",
            raw_text="launch release feature for llm agents",
        )
        trusted_score = score_item(item, trusted_profile)
        plain_score = score_item(item, plain_profile)
        self.assertEqual(trusted_score.quality, plain_score.quality)
        self.assertEqual(trusted_score.total, plain_score.total)

    def test_source_preference_is_soft_and_quality_gated(self):
        profile = ProfileConfig(trusted_sources=["example.com"])
        low_signal = Score(
            item_id="low",
            relevance=10,
            quality=12,
            novelty=4,
            total=26,
        )
        high_signal = Score(
            item_id="high",
            relevance=30,
            quality=18,
            novelty=7,
            total=55,
        )
        item = Item(
            id="pref-1",
            url="https://example.com/post",
            title="Strong AI benchmark",
            source="https://example.com/feed.xml",
            author=None,
            published_at=datetime.now(),
            type="article",
            raw_text="benchmark inference agents",
        )
        self.assertEqual(source_preference_adjustment(item, low_signal, profile), 0.0)
        self.assertEqual(source_preference_adjustment(item, high_signal, profile), 2.0)

    def test_research_concentration_adjustments_penalize_paper_heavy_pool(self):
        rows: list[ScoredItem] = []
        for idx in range(1, 6):
            item = Item(
                id=str(idx),
                url=f"https://arxiv.org/abs/{idx}",
                title=f"Paper {idx}",
                source="https://arxiv.org/rss/cs.LG",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="paper benchmark kv cache distillation",
            )
            score = Score(
                item_id=item.id,
                relevance=30,
                quality=20,
                novelty=10,
                total=100 - idx,
                format_tags=["paper", "technical"],
            )
            rows.append(ScoredItem(item=item, score=score))

        rows.append(
            ScoredItem(
                item=Item(
                    id="n1",
                    url="https://example.com/news",
                    title="AI product release",
                    source="https://example.com/feed",
                    author=None,
                    published_at=datetime.now(),
                    type="article",
                    raw_text="launch release feature",
                ),
                score=Score("n1", 20, 15, 8, 88, format_tags=["news"]),
            )
        )

        adjustments = research_concentration_adjustments(rows, pool_size=6)
        self.assertEqual(adjustments.get("1", 0.0), 0.0)
        self.assertEqual(adjustments.get("2", 0.0), 0.0)
        self.assertLess(adjustments.get("3", 0.0), 0.0)
        self.assertLess(adjustments.get("4", 0.0), adjustments.get("3", 0.0))
        self.assertLess(adjustments.get("5", 0.0), 0.0)

    def test_research_concentration_adjustments_do_not_penalize_small_mix(self):
        rows: list[ScoredItem] = []
        for idx in range(1, 4):
            item = Item(
                id=str(idx),
                url=f"https://arxiv.org/abs/{idx}",
                title=f"Paper {idx}",
                source="https://arxiv.org/rss/cs.AI",
                author=None,
                published_at=datetime.now(),
                type="article",
                raw_text="paper benchmark kv cache distillation",
            )
            score = Score(
                item_id=item.id,
                relevance=30,
                quality=20,
                novelty=10,
                total=100 - idx,
                format_tags=["paper", "technical"],
            )
            rows.append(ScoredItem(item=item, score=score))

        adjustments = research_concentration_adjustments(rows, pool_size=6)
        self.assertEqual(adjustments, {})


if __name__ == "__main__":
    unittest.main()
