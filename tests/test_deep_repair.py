import unittest
from datetime import datetime

from digest.models import Item, Score, ScoredItem
from digest.quality.deep_repair import DeepAgentQualityRepair


def _mk(idx: int, source: str = "https://e/x", total: int = 100) -> ScoredItem:
    item = Item(
        id=str(idx),
        url=f"https://e/{idx}",
        title=f"T{idx}",
        source=source,
        author=None,
        published_at=datetime.now(),
        type="article",
        raw_text="x",
    )
    return ScoredItem(item=item, score=Score(str(idx), 20, 10, 5, total))


class _FakeAgent:
    """Stands in for a compiled DeepAgents graph."""

    def __init__(self, structured_response=None, error: Exception | None = None):
        self._structured = structured_response
        self._error = error
        self.calls = 0
        self.last_input = None

    def invoke(self, state):
        self.calls += 1
        self.last_input = state
        if self._error is not None:
            raise self._error
        return {"structured_response": self._structured, "messages": []}


class TestDeepAgentQualityRepair(unittest.TestCase):
    def _pool(self) -> list[ScoredItem]:
        return [_mk(i, f"https://src/{i}") for i in range(1, 9)]

    def test_returns_validated_repair_result(self):
        pool = self._pool()
        current = pool[:5]
        agent = _FakeAgent(
            structured_response={
                "quality_score": 40.0,
                "confidence": 0.9,
                "issues": ["redundant sources"],
                "repaired_must_read_ids": ["1", "2", "3", "6", "7"],
            }
        )
        judge = DeepAgentQualityRepair(model="gpt-5.1-codex-mini", agent=agent)
        result = judge.evaluate_and_repair(
            current_must_read=current,
            candidate_pool=pool,
            must_read_max_per_source=2,
            digest_max_per_source=3,
        )
        self.assertEqual(result.repaired_must_read_ids, ["1", "2", "3", "6", "7"])
        self.assertEqual(result.quality_score, 40.0)
        self.assertEqual(result.model, "gpt-5.1-codex-mini")
        self.assertEqual(agent.calls, 1)

    def test_id_outside_pool_raises(self):
        pool = self._pool()
        agent = _FakeAgent(
            structured_response={
                "quality_score": 50.0,
                "confidence": 0.5,
                "issues": [],
                "repaired_must_read_ids": ["1", "2", "3", "4", "999"],
            }
        )
        judge = DeepAgentQualityRepair(model="m", agent=agent)
        with self.assertRaises(RuntimeError):
            judge.evaluate_and_repair(
                current_must_read=pool[:5],
                candidate_pool=pool,
                must_read_max_per_source=2,
                digest_max_per_source=3,
            )

    def test_agent_error_normalized(self):
        pool = self._pool()
        agent = _FakeAgent(error=ValueError("agent boom"))
        judge = DeepAgentQualityRepair(model="m", agent=agent)
        with self.assertRaises(RuntimeError) as cm:
            judge.evaluate_and_repair(
                current_must_read=pool[:5],
                candidate_pool=pool,
                must_read_max_per_source=2,
                digest_max_per_source=3,
            )
        self.assertIn("agent boom", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
