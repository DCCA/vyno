import unittest
from unittest.mock import patch

from digest.connectors.github import fetch_github_items


class TestGitHubConnector(unittest.TestCase):
    def test_maps_releases_issues_prs_repos(self):
        def fake_request(path, token, timeout):
            if path.startswith("/repos/openai/openai-cookbook/releases"):
                return [
                    {
                        "html_url": "https://github.com/openai/openai-cookbook/releases/tag/v1",
                        "name": "v1",
                        "body": "release notes",
                        "published_at": "2026-02-22T01:00:00Z",
                    }
                ]
            if path.startswith("/repos/openai/openai-cookbook/issues"):
                return [
                    {
                        "html_url": "https://github.com/openai/openai-cookbook/issues/1",
                        "title": "Issue title",
                        "body": "Issue body",
                        "updated_at": "2026-02-22T01:00:00Z",
                        "user": {"login": "alice"},
                    },
                    {
                        "html_url": "https://github.com/openai/openai-cookbook/pull/2",
                        "title": "PR title",
                        "body": "PR body",
                        "updated_at": "2026-02-22T01:00:00Z",
                        "user": {"login": "bob"},
                        "pull_request": {"url": "x"},
                    },
                ]
            if path.startswith("/search/repositories"):
                return {
                    "items": [
                        {
                            "html_url": "https://github.com/acme/agent-repo",
                            "full_name": "acme/agent-repo",
                            "description": "agent repo",
                            "updated_at": "2026-02-22T01:00:00Z",
                            "owner": {"login": "acme"},
                        }
                    ]
                }
            if path.startswith("/search/issues"):
                return {
                    "items": [
                        {
                            "html_url": "https://github.com/acme/agent-repo/issues/10",
                            "title": "search issue",
                            "body": "body",
                            "updated_at": "2026-02-22T01:00:00Z",
                            "repository_url": "https://api.github.com/repos/acme/agent-repo",
                            "user": {"login": "charlie"},
                        }
                    ]
                }
            return {}

        with patch("digest.connectors.github._request_json", side_effect=fake_request):
            items = fetch_github_items(
                repos=["openai/openai-cookbook"],
                topics=["llm"],
                queries=["repo:openai/openai-cookbook is:issue llm"],
                token="",
            )

        types = sorted({i.type for i in items})
        self.assertIn("github_release", types)
        self.assertIn("github_issue", types)
        self.assertIn("github_pr", types)
        self.assertIn("github_repo", types)
        self.assertGreaterEqual(len(items), 5)


if __name__ == "__main__":
    unittest.main()
