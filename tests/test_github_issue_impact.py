import unittest
from datetime import datetime

from digest.config import ProfileConfig
from digest.models import Item
from digest.pipeline.github_issue_impact import evaluate_github_issue_impact


class TestGitHubIssueImpact(unittest.TestCase):
    def test_keeps_trusted_org_issue_with_medium_keyword(self):
        profile = ProfileConfig(trusted_orgs_github=["anthropics"])
        item = Item(
            id="issue-1",
            url="https://github.com/anthropics/claude-code/issues/1",
            title="Regression causes outage in permissions flow",
            source="github:anthropics/claude-code",
            author="maintainer",
            published_at=datetime.now(),
            type="github_issue",
            raw_text="labels=bug,incident | comments=10",
            hash="issue-1-hash",
        )

        decision = evaluate_github_issue_impact(item, profile)
        self.assertTrue(decision.keep)
        self.assertTrue(decision.trusted_org)
        self.assertIn("regression", decision.matched_keywords)

    def test_drops_untrusted_org_even_with_keyword(self):
        profile = ProfileConfig(trusted_orgs_github=["anthropics"])
        item = Item(
            id="issue-2",
            url="https://github.com/random/repo/issues/2",
            title="Regression causes outage",
            source="github:random/repo",
            author="maintainer",
            published_at=datetime.now(),
            type="github_issue",
            raw_text="labels=bug",
            hash="issue-2-hash",
        )

        decision = evaluate_github_issue_impact(item, profile)
        self.assertFalse(decision.keep)
        self.assertEqual(decision.reason, "untrusted_org")

    def test_drops_trusted_org_without_medium_keyword(self):
        profile = ProfileConfig(trusted_orgs_github=["anthropics"])
        item = Item(
            id="issue-3",
            url="https://github.com/anthropics/claude-code/issues/3",
            title="Minor typo in docs",
            source="github:anthropics/claude-code",
            author="maintainer",
            published_at=datetime.now(),
            type="github_issue",
            raw_text="labels=docs | comments=1",
            hash="issue-3-hash",
        )

        decision = evaluate_github_issue_impact(item, profile)
        self.assertFalse(decision.keep)
        self.assertEqual(decision.reason, "missing_medium_signal")


if __name__ == "__main__":
    unittest.main()
