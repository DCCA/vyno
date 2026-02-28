from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from digest.models import Item, ItemType

API_BASE = "https://api.github.com"


def fetch_github_items(
    repos: list[str],
    topics: list[str],
    queries: list[str],
    orgs: list[str] | None = None,
    token: str = "",
    timeout: int = 20,
    org_options: dict | None = None,
) -> list[Item]:
    items: list[Item] = []
    org_opts = org_options or {}
    min_stars = max(0, int(org_opts.get("min_stars", 0) or 0))
    include_forks = bool(org_opts.get("include_forks", False))
    include_archived = bool(org_opts.get("include_archived", False))
    repo_max_age_days = max(1, int(org_opts.get("repo_max_age_days", 30) or 30))
    activity_max_age_days = max(1, int(org_opts.get("activity_max_age_days", 14) or 14))

    for repo in repos:
        items.extend(
            _fetch_repo_releases(
                repo,
                token,
                timeout,
                max_age_days=activity_max_age_days,
            )
        )
        items.extend(
            _fetch_repo_issues_and_prs(
                repo,
                token,
                timeout,
                max_age_days=activity_max_age_days,
            )
        )

    for topic in topics:
        items.extend(
            _search_repos_by_topic(
                topic,
                token,
                timeout,
                min_stars=min_stars,
                include_forks=include_forks,
                include_archived=include_archived,
                max_age_days=repo_max_age_days,
            )
        )

    for query in queries:
        items.extend(
            _search_issues_and_prs(
                query,
                token,
                timeout,
                max_age_days=activity_max_age_days,
            )
        )

    for org_raw in orgs or []:
        org = normalize_github_org(org_raw)
        if not org:
            continue
        items.extend(
            _fetch_org_repo_updates_and_releases(
                org=org,
                token=token,
                timeout=timeout,
                min_stars=min_stars,
                include_forks=include_forks,
                include_archived=include_archived,
                max_repos=int(org_opts.get("max_repos_per_org", 20) or 20),
                max_items=int(org_opts.get("max_items_per_org", 40) or 40),
                repo_max_age_days=repo_max_age_days,
                activity_max_age_days=activity_max_age_days,
            )
        )

    return items


def normalize_github_org(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    # Accept https://github.com/<org> and plain <org>.
    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urllib.parse.urlparse(raw)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            return ""
        path = parsed.path.strip("/")
        if not path:
            return ""
        org = path.split("/", 1)[0]
    else:
        org = raw.split("/", 1)[0].strip().lstrip("@")
    return org.lower()


def _is_recent(value: datetime | None, *, max_age_days: int) -> bool:
    if value is None:
        return False
    dt = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, max_age_days))
    return dt >= cutoff


def _fetch_org_repo_updates_and_releases(
    *,
    org: str,
    token: str,
    timeout: int,
    min_stars: int,
    include_forks: bool,
    include_archived: bool,
    max_repos: int,
    max_items: int,
    repo_max_age_days: int,
    activity_max_age_days: int,
) -> list[Item]:
    repos = _fetch_org_repos(org, token, timeout, max(1, min(100, max_repos * 2)))
    selected = _filter_org_repos(
        repos,
        min_stars=max(0, min_stars),
        include_forks=include_forks,
        include_archived=include_archived,
        max_age_days=max(1, repo_max_age_days),
    )[: max(1, max_repos)]

    out: list[Item] = []
    for repo in selected:
        full_name = str(repo.get("full_name") or "").strip()
        if not full_name:
            continue
        repo_item = _map_repo_update_item(repo)
        if repo_item is not None:
            out.append(repo_item)
            if len(out) >= max_items:
                break
        for rel in _fetch_repo_releases(
            full_name,
            token,
            timeout,
            max_age_days=max(1, activity_max_age_days),
        ):
            out.append(rel)
            if len(out) >= max_items:
                break
        if len(out) >= max_items:
            break
    return out


def _fetch_org_repos(org: str, token: str, timeout: int, per_page: int) -> list[dict]:
    path = f"/orgs/{org}/repos?sort=updated&direction=desc&per_page={per_page}"
    data = _request_json(path, token, timeout)
    return data if isinstance(data, list) else []


def _filter_org_repos(
    repos: list[dict],
    *,
    min_stars: int,
    include_forks: bool,
    include_archived: bool,
    max_age_days: int,
) -> list[dict]:
    out: list[dict] = []
    for repo in repos:
        stars = int(repo.get("stargazers_count") or 0)
        if stars < min_stars:
            continue
        if not include_forks and bool(repo.get("fork", False)):
            continue
        if not include_archived and bool(repo.get("archived", False)):
            continue
        updated = _parse_iso(str(repo.get("updated_at") or ""))
        if not _is_recent(updated, max_age_days=max_age_days):
            continue
        out.append(repo)
    return out


def _map_repo_update_item(repo: dict) -> Item | None:
    url = str(repo.get("html_url") or "").strip()
    full_name = str(repo.get("full_name") or "").strip()
    if not url or not full_name:
        return None
    desc = str(repo.get("description") or "")
    stars = int(repo.get("stargazers_count") or 0)
    lang = str(repo.get("language") or "").strip()
    updated = _parse_iso(str(repo.get("updated_at") or ""))
    owner = (
        str(
            ((repo.get("owner") or {}).get("login") or _extract_owner(full_name))
        ).strip()
        or None
    )
    details = [desc.strip(), f"stars={stars}"]
    if lang:
        details.append(f"language={lang}")
    return _make_item(
        url=url,
        title=full_name,
        source=f"github:{full_name}",
        author=owner,
        published_at=updated,
        item_type="github_repo",
        raw_text=" | ".join([d for d in details if d]),
    )


def _fetch_repo_releases(
    repo: str,
    token: str,
    timeout: int,
    *,
    max_age_days: int,
) -> list[Item]:
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
        if not _is_recent(pub, max_age_days=max_age_days):
            continue
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


def _fetch_repo_issues_and_prs(
    repo: str,
    token: str,
    timeout: int,
    *,
    max_age_days: int,
) -> list[Item]:
    path = f"/repos/{repo}/issues?state=open&per_page=5"
    data = _request_json(path, token, timeout)
    out: list[Item] = []
    for issue in data if isinstance(data, list) else []:
        url = str(issue.get("html_url", "")).strip()
        if not url:
            continue
        title = str(issue.get("title") or "Issue")
        body = str(issue.get("body") or "")
        labels = _extract_issue_labels(issue.get("labels"))
        comments = int(issue.get("comments") or 0)
        pub = _parse_iso(str(issue.get("updated_at") or issue.get("created_at") or ""))
        if not _is_recent(pub, max_age_days=max_age_days):
            continue
        user = issue.get("user") or {}
        author = str(user.get("login") or "") or _extract_owner(repo)
        item_type: ItemType = (
            "github_pr" if issue.get("pull_request") else "github_issue"
        )
        out.append(
            _make_item(
                url=url,
                title=title,
                source=f"github:{repo}",
                author=author,
                published_at=pub,
                item_type=item_type,
                raw_text=_compose_issue_raw_text(body, labels, comments),
            )
        )
    return out


def _search_repos_by_topic(
    topic: str,
    token: str,
    timeout: int,
    *,
    min_stars: int,
    include_forks: bool,
    include_archived: bool,
    max_age_days: int,
) -> list[Item]:
    q = urllib.parse.quote_plus(f"topic:{topic}")
    path = f"/search/repositories?q={q}&sort=updated&order=desc&per_page=5"
    data = _request_json(path, token, timeout)
    out: list[Item] = []
    for repo in data.get("items", []) if isinstance(data, dict) else []:
        url = str(repo.get("html_url", "")).strip()
        if not url:
            continue
        stars = int(repo.get("stargazers_count") or 0)
        if stars < min_stars:
            continue
        if not include_forks and bool(repo.get("fork", False)):
            continue
        if not include_archived and bool(repo.get("archived", False)):
            continue
        full_name = str(repo.get("full_name") or "")
        title = full_name or str(repo.get("name") or "Repository")
        desc = str(repo.get("description") or "")
        pub = _parse_iso(str(repo.get("updated_at") or ""))
        if not _is_recent(pub, max_age_days=max_age_days):
            continue
        owner = (
            (repo.get("owner") or {}).get("login") or _extract_owner(full_name or "")
        ).strip()
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


def _search_issues_and_prs(
    query: str,
    token: str,
    timeout: int,
    *,
    max_age_days: int,
) -> list[Item]:
    q = urllib.parse.quote_plus(query)
    path = f"/search/issues?q={q}&sort=updated&order=desc&per_page=5"
    data = _request_json(path, token, timeout)
    out: list[Item] = []
    for issue in data.get("items", []) if isinstance(data, dict) else []:
        url = str(issue.get("html_url", "")).strip()
        if not url:
            continue
        title = str(issue.get("title") or "Issue")
        body = str(issue.get("body") or "")
        labels = _extract_issue_labels(issue.get("labels"))
        comments = int(issue.get("comments") or 0)
        pub = _parse_iso(str(issue.get("updated_at") or issue.get("created_at") or ""))
        if not _is_recent(pub, max_age_days=max_age_days):
            continue
        repo_url = str(issue.get("repository_url") or "")
        repo = repo_url.split("/repos/")[-1] if "/repos/" in repo_url else "search"
        user = issue.get("user") or {}
        author = str(user.get("login") or "") or _extract_owner(repo)
        item_type: ItemType = (
            "github_pr"
            if "pull" in str(issue.get("html_url") or "")
            else "github_issue"
        )
        out.append(
            _make_item(
                url=url,
                title=title,
                source=f"github:{repo}",
                author=author,
                published_at=pub,
                item_type=item_type,
                raw_text=_compose_issue_raw_text(body, labels, comments),
            )
        )
    return out


def _extract_issue_labels(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    labels: list[str] = []
    for entry in raw:
        if isinstance(entry, dict):
            name = str(entry.get("name") or "").strip().lower()
        else:
            name = str(entry or "").strip().lower()
        if name and name not in labels:
            labels.append(name)
    return labels


def _compose_issue_raw_text(body: str, labels: list[str], comments: int) -> str:
    details = [body.strip()]
    if labels:
        details.append(f"labels={','.join(labels)}")
    details.append(f"comments={max(0, comments)}")
    return " | ".join([d for d in details if d])


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
    item_type: ItemType,
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
