import unittest
from types import SimpleNamespace

from digest.web.app import (
    _count_fetch_targets,
    _estimate_run_progress_percent,
    _run_stage_detail,
    _run_stage_label,
)


class TestWebRunProgress(unittest.TestCase):
    def test_count_fetch_targets(self):
        sources = SimpleNamespace(
            rss_feeds=["a", "b"],
            youtube_channels=["c1"],
            youtube_queries=["q1", "q2"],
            x_inbox_path="data/x_inbox.txt",
            github_repos=["owner/repo"],
            github_topics=[],
            github_search_queries=[],
            github_orgs=[],
        )
        self.assertEqual(_count_fetch_targets(sources), 7)

    def test_estimate_progress_for_fetch_and_score(self):
        self.assertAlmostEqual(
            _estimate_run_progress_percent(
                "fetch_rss",
                details={"fetch_done": 2, "fetch_total": 4},
                fetch_done=2,
                fetch_total=4,
            ),
            20.0,
        )
        self.assertAlmostEqual(
            _estimate_run_progress_percent(
                "score_progress",
                details={"processed_count": 20, "total_count": 40},
                fetch_done=0,
                fetch_total=0,
            ),
            58.0,
        )

    def test_stage_label_and_detail(self):
        self.assertEqual(_run_stage_label("score_progress"), "Scoring Items")
        detail = _run_stage_detail(
            "summarize_progress",
            {
                "processed_count": 5,
                "total_count": 10,
                "fallback_count": 2,
            },
            fallback="Working",
        )
        self.assertIn("Summarized 5/10", detail)
        self.assertIn("fallback", detail)


if __name__ == "__main__":
    unittest.main()
