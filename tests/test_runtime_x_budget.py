import unittest

from digest.runtime import _plan_x_selector_limits, _x_posts_budget_per_run


class TestRuntimeXBudget(unittest.TestCase):
    def test_budget_uses_spend_and_cost(self):
        self.assertEqual(
            _x_posts_budget_per_run(max_spend_usd=0.05, cost_per_post_usd=0.005),
            10,
        )

    def test_budget_zero_disables_x_fetch(self):
        self.assertEqual(
            _x_posts_budget_per_run(max_spend_usd=0.0, cost_per_post_usd=0.005),
            0,
        )

    def test_author_priority_consumes_budget_before_themes(self):
        plan = _plan_x_selector_limits(
            authors=["alice", "bob"],
            themes=["ai agents"],
            max_spend_usd=0.05,
            cost_per_post_usd=0.005,
        )
        self.assertEqual(plan["post_budget"], 10)
        self.assertEqual(plan["author_budget"], 10)
        self.assertEqual(plan["theme_budget"], 0)
        self.assertEqual(plan["author_limits"], {"alice": 5, "bob": 5})
        self.assertEqual(plan["theme_limits"], {"ai agents": 0})


if __name__ == "__main__":
    unittest.main()
