"""Detect which connector can ingest a pasted URL or handle.

Powers `/source add <url-or-handle>` in the Telegram bot: try the specific
connectors first, fall back to RSS autodiscovery, and return an "unknown"
detection (empty source_type) when nothing fits so the caller can log an
ingest suggestion instead of dead-ending.
"""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable

from digest.ops.source_registry import canonicalize_source_value

FETCH_TIMEOUT_SECONDS = 4
MAX_FETCH_BYTES = 256 * 1024
_USER_AGENT = "ai-daily-digest/1.0 (+source-detect)"

_YT_CHANNEL_ID_RE = re.compile(r"UC[0-9A-Za-z_-]{22}")
_FEED_LINK_RE = re.compile(
    r"<link[^>]+rel=[\"']alternate[\"'][^>]+type=[\"']application/(?:rss|atom)\+xml[\"'][^>]*>",
    re.IGNORECASE,
)
_HREF_RE = re.compile(r"href=[\"']([^\"']+)[\"']", re.IGNORECASE)


@dataclass(slots=True)
class IngestDetection:
    source_type: str  # "" means no connector handles it (ingest suggestion)
    value: str
    note: str = ""


def _default_fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_SECONDS) as resp:
        return resp.read(MAX_FETCH_BYTES).decode("utf-8", errors="replace")


def detect_ingest(
    raw: str, fetch: Callable[[str], str] | None = None
) -> IngestDetection | None:
    """Return the detected source for a pasted value, or None if it is not
    a URL/handle at all. source_type == "" means "no connector fits"."""
    value = (raw or "").strip()
    fetch = fetch or _default_fetch

    if value.startswith("@"):
        return _try(("x_author", value))

    if _YT_CHANNEL_ID_RE.fullmatch(value):
        return IngestDetection("youtube_channel", value)

    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    host = parsed.netloc.lower().removeprefix("www.")
    path_parts = [p for p in parsed.path.split("/") if p]

    if host == "github.com" and path_parts:
        if len(path_parts) >= 2:
            return _try(("github_repo", f"{path_parts[0]}/{path_parts[1]}"))
        return _try(("github_org", path_parts[0]))

    if host in {"x.com", "twitter.com"}:
        return _try(("x_author", value))

    if host in {"youtube.com", "m.youtube.com", "youtu.be"}:
        if len(path_parts) >= 2 and path_parts[0] == "channel":
            match = _YT_CHANNEL_ID_RE.fullmatch(path_parts[1])
            if match:
                return IngestDetection("youtube_channel", match.group(0))
        try:
            page = fetch(value)
        except Exception:
            return IngestDetection("", value, note="unreachable")
        match = _YT_CHANNEL_ID_RE.search(page)
        if match:
            return IngestDetection("youtube_channel", match.group(0))
        return IngestDetection("", value, note="no channel id found on page")

    # Anything else over http(s): direct feed, else autodiscovery, else unknown.
    try:
        body = fetch(value)
    except Exception:
        return IngestDetection("", value, note="unreachable")
    head = body.lstrip()[:200].lower()
    if head.startswith("<?xml") or "<rss" in head or "<feed" in head:
        return IngestDetection("rss", value)
    link_tag = _FEED_LINK_RE.search(body)
    if link_tag:
        href = _HREF_RE.search(link_tag.group(0))
        if href:
            feed_url = urllib.parse.urljoin(value, href.group(1))
            return IngestDetection("rss", feed_url, note="feed discovered on page")
    return IngestDetection("", value, note="no feed found")


def _try(candidate: tuple[str, str]) -> IngestDetection | None:
    source_type, raw_value = candidate
    try:
        return IngestDetection(source_type, canonicalize_source_value(source_type, raw_value))
    except ValueError:
        return IngestDetection("", raw_value, note=f"not a valid {source_type}")
