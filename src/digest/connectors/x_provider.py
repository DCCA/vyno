from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class XPostPayload:
    id: str
    text: str
    author_username: str
    created_at: datetime | None
    url: str
    outbound_urls: list[str]


class XProvider:
    def fetch_author_posts(
        self,
        *,
        author: str,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[XPostPayload], str | None]:
        raise NotImplementedError

    def fetch_theme_posts(
        self,
        *,
        query: str,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[XPostPayload], str | None]:
        raise NotImplementedError


class InboxOnlyXProvider(XProvider):
    def _unsupported(self) -> Exception:
        return RuntimeError(
            "DIGEST_X_PROVIDER=inbox_only does not support x_author/x_theme selectors"
        )

    def fetch_author_posts(
        self,
        *,
        author: str,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[XPostPayload], str | None]:
        raise self._unsupported()

    def fetch_theme_posts(
        self,
        *,
        query: str,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[XPostPayload], str | None]:
        raise self._unsupported()


class XApiProvider(XProvider):
    def __init__(self, *, bearer_token: str, timeout: int = 20) -> None:
        self._bearer_token = (bearer_token or "").strip()
        if not self._bearer_token:
            raise RuntimeError("X_BEARER_TOKEN is required for DIGEST_X_PROVIDER=x_api")
        self._timeout = max(5, int(timeout))
        self._username_cache: dict[str, str] = {}

    def fetch_author_posts(
        self,
        *,
        author: str,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[XPostPayload], str | None]:
        username = author.strip().lstrip("@").lower()
        user_id = self._resolve_user_id(username)
        params: dict[str, str] = {
            "max_results": str(_bound_limit(limit)),
            "exclude": "retweets,replies",
            "tweet.fields": "created_at,entities",
        }
        if cursor:
            params["pagination_token"] = cursor
        payload = self._request_json(f"/2/users/{user_id}/tweets", params)
        data = payload.get("data", []) if isinstance(payload, dict) else []
        posts = [
            _map_tweet_to_payload(row, fallback_username=username)
            for row in data
            if isinstance(row, dict)
        ]
        posts = [p for p in posts if p is not None]
        next_cursor = _extract_next_cursor(payload)
        return posts, next_cursor

    def fetch_theme_posts(
        self,
        *,
        query: str,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[XPostPayload], str | None]:
        params: dict[str, str] = {
            "query": query,
            "max_results": str(_bound_limit(limit)),
            "tweet.fields": "created_at,author_id,entities",
            "expansions": "author_id",
            "user.fields": "username",
        }
        if cursor:
            params["next_token"] = cursor
        payload = self._request_json("/2/tweets/search/recent", params)
        includes = payload.get("includes", {}) if isinstance(payload, dict) else {}
        users = includes.get("users", []) if isinstance(includes, dict) else []
        user_map = {
            str(row.get("id") or ""): str(row.get("username") or "").strip().lower()
            for row in users
            if isinstance(row, dict)
        }
        data = payload.get("data", []) if isinstance(payload, dict) else []
        posts = [
            _map_tweet_to_payload(
                row,
                fallback_username=user_map.get(str(row.get("author_id") or ""), "unknown"),
            )
            for row in data
            if isinstance(row, dict)
        ]
        posts = [p for p in posts if p is not None]
        next_cursor = _extract_next_cursor(payload)
        return posts, next_cursor

    def _resolve_user_id(self, username: str) -> str:
        if username in self._username_cache:
            return self._username_cache[username]
        payload = self._request_json(
            f"/2/users/by/username/{urllib.parse.quote(username, safe='')}",
            {"user.fields": "username"},
        )
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        user_id = str(data.get("id") or "").strip()
        if not user_id:
            raise RuntimeError(f"X API user lookup failed for @{username}")
        self._username_cache[username] = user_id
        return user_id

    def _request_json(self, path: str, params: dict[str, str]) -> dict:
        query = urllib.parse.urlencode(params)
        url = f"https://api.x.com{path}"
        if query:
            url = f"{url}?{query}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self._bearer_token}",
                "Accept": "application/json",
                "User-Agent": "ai-digest/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected X API response payload")
        return data


def get_x_provider(mode: str = "") -> XProvider:
    selected = (mode or os.getenv("DIGEST_X_PROVIDER", "inbox_only")).strip().lower()
    if selected in {"", "inbox_only"}:
        return InboxOnlyXProvider()
    if selected == "x_api":
        return XApiProvider(
            bearer_token=os.getenv("X_BEARER_TOKEN", ""),
            timeout=int(os.getenv("DIGEST_X_API_TIMEOUT", "20") or "20"),
        )
    raise RuntimeError(f"Unsupported DIGEST_X_PROVIDER '{selected}'")


def _bound_limit(value: int) -> int:
    if value <= 0:
        return 10
    return max(10, min(100, int(value)))


def _extract_next_cursor(payload: dict) -> str | None:
    if not isinstance(payload, dict):
        return None
    meta = payload.get("meta", {})
    if not isinstance(meta, dict):
        return None
    next_token = str(meta.get("next_token") or meta.get("pagination_token") or "").strip()
    return next_token or None


def _parse_datetime(raw: str) -> datetime | None:
    value = (raw or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _extract_outbound_urls(tweet: dict) -> list[str]:
    entities = tweet.get("entities", {})
    if not isinstance(entities, dict):
        return []
    urls = entities.get("urls", [])
    if not isinstance(urls, list):
        return []
    values: list[str] = []
    for row in urls:
        if not isinstance(row, dict):
            continue
        expanded = str(row.get("expanded_url") or row.get("url") or "").strip()
        if not expanded:
            continue
        values.append(expanded)
    return values


def _map_tweet_to_payload(tweet: dict, *, fallback_username: str) -> XPostPayload | None:
    tweet_id = str(tweet.get("id") or "").strip()
    if not tweet_id:
        return None
    username = (fallback_username or "unknown").strip().lstrip("@").lower() or "unknown"
    text = str(tweet.get("text") or "").strip()
    outbound = _extract_outbound_urls(tweet)
    return XPostPayload(
        id=tweet_id,
        text=text,
        author_username=username,
        created_at=_parse_datetime(str(tweet.get("created_at") or "")),
        url=f"https://x.com/{username}/status/{tweet_id}",
        outbound_urls=outbound,
    )
