from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

from digest.models import Item

API_BASE = "https://api.github.com"


def fetch_github_items(
    repos: list[str],
    topics: list[str],
    queries: list[str],
    token: str = "",
    timeout: int = 20,
) -> list[Item]:
    items: list[Item] = []

    for repo in repos:
        items.extend(_fetch_repo_releases(repo, token, timeout))
        items.extend(_fetch_repo_issues_and_prs(repo, token, timeout))

    for topic in topics:
        items.extend(_search_repos_by_topic(topic, token, timeout))

    for query in queries:
        items.extend(_search_issues_and_prs(query, token, timeout))

    return items


def _fetch_repo_releases(repo: str, token: str, timeout: int) -> list[Item]:
    path = f"/repos/{repo}/releases?per_page=5"
    data = _request_json(path, token, timeout)
    out: list[Item] = []
    for rel in data if isinstance(data, list) else []:
        url = str(rel.get("html_url", "")).strip()
        if not url:
            continue
        title = str(rel.get("name") or rel.get("tag_name") or f"Release {repo}")
        raw_text = str(rel.get("body") or "")
        pub = _parse_iso(str(rel.get("published_at") or ""))
        owner = _extract_owner(repo)
        out.append(
            _make_item(
                url=url,
                title=title,
                source=f"github:{repo}",
                author=owner,
                published_at=pub,
                item_type="github_release",
                raw_text=raw_text,
            )
        )
    return out


def _fetch_repo_issues_and_prs(repo: str, token: str, timeout: int) -> list[Item]:
    path = f"/repos/{repo}/issues?state=open&per_page=5"
    data = _request_json(path, token, timeout)
    out: list[Item] = []
    for issue in data if isinstance(data, list) else []:
        url = str(issue.get("html_url", "")).strip()
        if not url:
            continue
        title = str(issue.get("title") or "Issue")
        body = str(issue.get("body") or "")
        pub = _parse_iso(str(issue.get("updated_at") or issue.get("created_at") or ""))
        user = issue.get("user") or {}
        author = str(user.get("login") or "") or _extract_owner(repo)
        item_type = "github_pr" if issue.get("pull_request") else "github_issue"
        out.append(
            _make_item(
                url=url,
                title=title,
                source=f"github:{repo}",
                author=author,
                published_at=pub,
                item_type=item_type,
                raw_text=body,
            )
        )
    return out


def _search_repos_by_topic(topic: str, token: str, timeout: int) -> list[Item]:
    q = urllib.parse.quote_plus(f"topic:{topic}")
    path = f"/search/repositories?q={q}&sort=updated&order=desc&per_page=5"
    data = _request_json(path, token, timeout)
    out: list[Item] = []
    for repo in (data.get("items", []) if isinstance(data, dict) else []):
        url = str(repo.get("html_url", "")).strip()
        if not url:
            continue
        full_name = str(repo.get("full_name") or "")
        title = full_name or str(repo.get("name") or "Repository")
        desc = str(repo.get("description") or "")
        pub = _parse_iso(str(repo.get("updated_at") or ""))
        owner = ((repo.get("owner") or {}).get("login") or _extract_owner(full_name or "")).strip()
        out.append(
            _make_item(
                url=url,
                title=title,
                source=f"github:{full_name}" if full_name else "github:search",
                author=owner,
                published_at=pub,
                item_type="github_repo",
                raw_text=desc,
            )
        )
    return out


def _search_issues_and_prs(query: str, token: str, timeout: int) -> list[Item]:
    q = urllib.parse.quote_plus(query)
    path = f"/search/issues?q={q}&sort=updated&order=desc&per_page=5"
    data = _request_json(path, token, timeout)
    out: list[Item] = []
    for issue in (data.get("items", []) if isinstance(data, dict) else []):
        url = str(issue.get("html_url", "")).strip()
        if not url:
            continue
        title = str(issue.get("title") or "Issue")
        body = str(issue.get("body") or "")
        pub = _parse_iso(str(issue.get("updated_at") or issue.get("created_at") or ""))
        repo_url = str(issue.get("repository_url") or "")
        repo = repo_url.split("/repos/")[-1] if "/repos/" in repo_url else "search"
        user = issue.get("user") or {}
        author = str(user.get("login") or "") or _extract_owner(repo)
        item_type = "github_pr" if "pull" in str(issue.get("html_url") or "") else "github_issue"
        out.append(
            _make_item(
                url=url,
                title=title,
                source=f"github:{repo}",
                author=author,
                published_at=pub,
                item_type=item_type,
                raw_text=body,
            )
        )
    return out


def _request_json(path: str, token: str, timeout: int) -> dict | list:
    req = urllib.request.Request(
        API_BASE + path,
        headers={
            "User-Agent": "ai-digest/1.0",
            "Accept": "application/vnd.github+json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub API HTTPError: {exc.code} ({path})") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub API connection error ({path})") from exc


def _make_item(
    *,
    url: str,
    title: str,
    source: str,
    author: str | None,
    published_at: datetime | None,
    item_type: str,
    raw_text: str,
) -> Item:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return Item(
        id=digest[:16],
        url=url,
        title=title.strip() or "Untitled",
        source=source,
        author=(author or None),
        published_at=published_at,
        type=item_type,
        raw_text=(raw_text or "").strip(),
        description=(raw_text or "").strip()[:400],
        hash=digest,
    )


def _parse_iso(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _extract_owner(repo: str) -> str:
    if "/" in repo:
        return repo.split("/", 1)[0]
    return repo
