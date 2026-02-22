import unittest
from unittest.mock import patch

from digest.connectors.github import fetch_github_items, normalize_github_org


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
                orgs=[],
                token="",
            )

        types = sorted({i.type for i in items})
        self.assertIn("github_release", types)
        self.assertIn("github_issue", types)
        self.assertIn("github_pr", types)
        self.assertIn("github_repo", types)
        self.assertGreaterEqual(len(items), 5)

    def test_normalize_github_org_accepts_url_and_login(self):
        self.assertEqual(normalize_github_org("https://github.com/vercel-labs"), "vercel-labs")
        self.assertEqual(normalize_github_org("vercel-labs"), "vercel-labs")
        self.assertEqual(normalize_github_org("@OpenAI"), "openai")

    def test_org_ingestion_emits_repo_and_release_only(self):
        def fake_request(path, token, timeout):
            if path.startswith("/orgs/vercel-labs/repos"):
                return [
                    {
                        "html_url": "https://github.com/vercel-labs/ai-sdk",
                        "full_name": "vercel-labs/ai-sdk",
                        "description": "AI SDK",
                        "updated_at": "2026-02-22T01:00:00Z",
                        "stargazers_count": 5000,
                        "fork": False,
                        "archived": False,
                        "language": "TypeScript",
                        "owner": {"login": "vercel-labs"},
                    }
                ]
            if path.startswith("/repos/vercel-labs/ai-sdk/releases"):
                return [
                    {
                        "html_url": "https://github.com/vercel-labs/ai-sdk/releases/tag/v1.0.0",
                        "name": "v1.0.0",
                        "body": "release notes",
                        "published_at": "2026-02-22T01:30:00Z",
                    }
                ]
            if path.startswith("/repos/vercel-labs/ai-sdk/issues"):
                raise AssertionError("Org mode should not request issues/PRs")
            return {}

        with patch("digest.connectors.github._request_json", side_effect=fake_request):
            items = fetch_github_items(
                repos=[],
                topics=[],
                queries=[],
                orgs=["https://github.com/vercel-labs"],
                token="",
                org_options={
                    "min_stars": 1,
                    "include_forks": False,
                    "include_archived": False,
                    "max_repos_per_org": 10,
                    "max_items_per_org": 10,
                },
            )
        types = {i.type for i in items}
        self.assertEqual(types, {"github_repo", "github_release"})
        self.assertEqual(len(items), 2)


if __name__ == "__main__":
    unittest.main()
