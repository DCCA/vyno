from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

from digest.models import Item

X_URL_RE = re.compile(r"https?://(?:x\.com|twitter\.com)/[A-Za-z0-9_]{1,15}/status/\d+")


def fetch_x_inbox_items(inbox_path: str) -> list[Item]:
    if not inbox_path:
        return []
    path = Path(inbox_path).expanduser()
    if not path.exists() or not path.is_file():
        return []

    items: list[Item] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        match = X_URL_RE.search(raw)
        if not match:
            continue
        url = match.group(0)
        comment = raw.replace(url, "", 1).strip(" -|\t")
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
