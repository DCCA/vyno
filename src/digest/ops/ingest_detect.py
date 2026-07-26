"""Detect which connector can ingest a pasted URL or handle.

Powers `/source add <url-or-handle>` in the Telegram bot: try the specific
connectors first, fall back to RSS autodiscovery, and return an "unknown"
detection (empty source_type) when nothing fits so the caller can log an
ingest suggestion instead of dead-ending.
"""

from __future__ import annotations

from html.parser import HTMLParser
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable

from digest.ops.source_registry import canonicalize_source_value

FETCH_TIMEOUT_SECONDS = 4
MAX_FETCH_BYTES = 256 * 1024
_USER_AGENT = "ai-daily-digest/1.0 (+source-detect)"

# Bare id validation only - never trust an unanchored match inside a page.
_YT_CHANNEL_ID_RE = re.compile(r"UC[0-9A-Za-z_-]{22}")
_YT_PAGE_CHANNEL_ID_RE = re.compile(r'"channelId"\s*:\s*"(UC[0-9A-Za-z_-]{22})"')
_YT_CHANNEL_PATH_RE = re.compile(r"/channel/(UC[0-9A-Za-z_-]{22})")

_FEED_TYPES = {"application/rss+xml", "application/atom+xml"}

# github.com paths that are product routes, not owners/repos.
_GITHUB_RESERVED_PATHS = {
    "about",
    "apps",
    "features",
    "login",
    "marketplace",
    "orgs",
    "topics",
    "trending",
    "collections",
    "sponsors",
    "settings",
    "notifications",
    "issues",
    "pulls",
    "explore",
    "new",
}

# fetch(url) -> (final_url_after_redirects, body)
Fetcher = Callable[[str], tuple[str, str]]


@dataclass(slots=True)
class IngestDetection:
    source_type: str  # "" means no connector handles it (ingest suggestion)
    value: str
    note: str = ""
    invalid: bool = False  # value failed validation - do not log as a suggestion


class _PageParser(HTMLParser):
    """Attribute-order-independent scan for feed <link>s and <meta> values."""

    def __init__(self) -> None:
        super().__init__()
        self.feed_href = ""
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered not in {"link", "meta"}:
            return
        attr_map = {str(key).lower(): str(value or "") for key, value in attrs}
        if lowered == "link":
            if self.feed_href:
                return
            rel = attr_map.get("rel", "").lower().split()
            content_type = attr_map.get("type", "").strip().lower()
            if "alternate" in rel and content_type in _FEED_TYPES:
                self.feed_href = attr_map.get("href", "").strip()
            return
        key = (
            attr_map.get("itemprop")
            or attr_map.get("property")
            or attr_map.get("name")
            or ""
        ).strip().lower()
        content = (attr_map.get("content") or "").strip()
        if key and content and key not in self.meta:
            self.meta[key] = content


def _parse_page(body: str) -> _PageParser:
    parser = _PageParser()
    parser.feed(body)
    return parser


def _default_fetch(url: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_SECONDS) as resp:
        final_url = str(resp.geturl() or url)
        return final_url, resp.read(MAX_FETCH_BYTES).decode("utf-8", errors="replace")


def detect_ingest(raw: str, fetch: Fetcher | None = None) -> IngestDetection | None:
    """Return the detected source for a pasted value, or None if it is not
    a URL/handle at all. source_type == "" means "no connector fits"."""
    value = (raw or "").strip()
    fetch = fetch or _default_fetch

    if value.startswith("@"):
        return _try("x_author", value)

    if _YT_CHANNEL_ID_RE.fullmatch(value):
        return IngestDetection("youtube_channel", value)

    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    host = parsed.netloc.lower().removeprefix("www.")
    path_parts = [p for p in parsed.path.split("/") if p]

    if host == "github.com" and path_parts:
        first = path_parts[0].lower()
        if len(path_parts) >= 2 and first == "orgs":
            return _try("github_org", path_parts[1])
        if len(path_parts) >= 2 and first == "topics":
            return _try("github_topic", path_parts[1])
        if first in _GITHUB_RESERVED_PATHS:
            return IngestDetection("", value, note="not a GitHub repo or org URL")
        if len(path_parts) >= 2:
            return _try("github_repo", f"{path_parts[0]}/{path_parts[1]}")
        return _try("github_org", path_parts[0])

    if host in {"x.com", "twitter.com"}:
        return _try("x_author", value)

    if host in {"youtube.com", "m.youtube.com", "youtu.be"}:
        if len(path_parts) >= 2 and path_parts[0] == "channel":
            match = _YT_CHANNEL_ID_RE.fullmatch(path_parts[1])
            if match:
                return IngestDetection("youtube_channel", match.group(0))
        try:
            _, page = fetch(value)
        except Exception:
            return IngestDetection("", value, note="unreachable")
        channel_id = _channel_id_from_page(page)
        if channel_id:
            return IngestDetection("youtube_channel", channel_id)
        return IngestDetection("", value, note="no channel id found on page")

    # Anything else over http(s): direct feed, else autodiscovery, else unknown.
    try:
        final_url, body = fetch(value)
    except Exception:
        return IngestDetection("", value, note="unreachable")
    head = body.lstrip()[:200].lower()
    if head.startswith("<?xml") or "<rss" in head or "<feed" in head:
        return IngestDetection("rss", value)
    href = _parse_page(body).feed_href
    if href:
        feed_url = urllib.parse.urljoin(final_url or value, href)
        return IngestDetection("rss", feed_url, note="feed discovered on page")
    return IngestDetection("", value, note="no feed found")


def _channel_id_from_page(page: str) -> str:
    """Pull the channel id from anchored markers only - a bare UC... match can
    hit a related channel or any 24-char substring."""
    match = _YT_PAGE_CHANNEL_ID_RE.search(page)
    if match:
        return match.group(1)
    meta = _parse_page(page).meta
    identifier = meta.get("identifier", "")
    if _YT_CHANNEL_ID_RE.fullmatch(identifier):
        return identifier
    match = _YT_CHANNEL_PATH_RE.search(meta.get("og:url", ""))
    return match.group(1) if match else ""


def _try(source_type: str, raw_value: str) -> IngestDetection:
    try:
        return IngestDetection(source_type, canonicalize_source_value(source_type, raw_value))
    except ValueError as exc:
        return IngestDetection(
            "", raw_value, note=f"not a valid {source_type}: {exc}", invalid=True
        )
