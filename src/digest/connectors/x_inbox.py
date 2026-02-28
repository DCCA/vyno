from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
import urllib.parse

from digest.models import Item

X_URL_RE = re.compile(r"https?://(?:x\.com|twitter\.com)/[A-Za-z0-9_]{1,15}/status/\d+")
LOW_SIGNAL_RE = re.compile(
    r"\b(giveaway|airdrop|follow\s+me|retweet|like\s+and\s+subscribe|promo\s+code|join\s+now|dm\s+me)\b",
    re.IGNORECASE,
)


def fetch_x_inbox_items(inbox_path: str) -> list[Item]:
    if not inbox_path:
        return []
    path = Path(inbox_path).expanduser()
    if not path.exists() or not path.is_file():
        return []

    items: list[Item] = []
    seen_urls: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        match = X_URL_RE.search(raw)
        if not match:
            continue
        raw_url = match.group(0)
        url = _canonicalize_x_url(raw_url)
        if not url or url in seen_urls:
            continue
        comment = raw.replace(raw_url, "", 1).strip(" -|\t")
        if comment and _is_low_signal_comment(comment):
            continue
        seen_urls.add(url)
        handle = _extract_handle(url)
        title = f"X post by @{handle}" if handle else "X post"
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        items.append(
            Item(
                id=digest[:16],
                url=url,
                title=title,
                source="x.com",
                author=handle,
                published_at=datetime.now(timezone.utc),
                type="x_post",
                raw_text=comment,
                description=comment,
                hash=digest,
            )
        )
    return items


def _extract_handle(url: str) -> str | None:
    try:
        parts = url.split("/")
        # https://x.com/<handle>/status/<id>
        return parts[3] if len(parts) > 4 else None
    except Exception:
        return None


def _canonicalize_x_url(url: str) -> str:
    parsed = urllib.parse.urlparse((url or "").strip())
    if parsed.netloc.lower() not in {
        "x.com",
        "twitter.com",
        "www.x.com",
        "www.twitter.com",
    }:
        return ""
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 3 or parts[1] != "status" or not parts[2].isdigit():
        return ""
    handle = parts[0]
    status_id = parts[2]
    return f"https://x.com/{handle}/status/{status_id}"


def _is_low_signal_comment(comment: str) -> bool:
    text = " ".join((comment or "").split()).strip()
    if not text:
        return False
    if LOW_SIGNAL_RE.search(text):
        return True
    alnum = re.sub(r"[^A-Za-z0-9]+", "", text)
    if len(alnum) < 8:
        return True
    return False
