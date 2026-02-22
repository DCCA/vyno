from __future__ import annotations

import hashlib
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

from digest.models import Item

TAG_RE = re.compile(r"<[^>]+>")
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def _strip_html(text: str) -> str:
    return TAG_RE.sub(" ", text or "").strip()


def fetch_rss_items(feed_urls: list[str], timeout: int = 15) -> list[Item]:
    items: list[Item] = []
    for feed_url in feed_urls:
        with urllib.request.urlopen(feed_url, timeout=timeout) as resp:
            content = resp.read()
        items.extend(parse_feed_items(feed_url, content))
    return items


def parse_feed_items(feed_url: str, content: bytes) -> list[Item]:
    root = ET.fromstring(content)
    if root.tag.endswith("rss"):
        return _parse_rss_channel(feed_url, root)
    if root.tag == f"{ATOM_NS}feed" or root.tag.endswith("feed"):
        return _parse_atom_feed(feed_url, root)
    return []


def _parse_rss_channel(feed_url: str, root: ET.Element) -> list[Item]:
    channel = root.find("channel")
    if channel is None:
        return []
    items: list[Item] = []
    for entry in channel.findall("item"):
        title = (entry.findtext("title") or "Untitled").strip()
        url = (entry.findtext("link") or "").strip()
        desc = _strip_html(entry.findtext("description") or "")
        pub = entry.findtext("pubDate")
        published_at = _parse_datetime(pub)
        author = entry.findtext("author")
        items.append(_to_item(feed_url, title, url, desc, published_at, author))
    return items


def _parse_atom_feed(feed_url: str, root: ET.Element) -> list[Item]:
    items: list[Item] = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        title = (entry.findtext(f"{ATOM_NS}title") or "Untitled").strip()
        link_el = entry.find(f"{ATOM_NS}link")
        url = ""
        if link_el is not None:
            url = (link_el.attrib.get("href") or "").strip()
        summary = _strip_html(entry.findtext(f"{ATOM_NS}summary") or entry.findtext(f"{ATOM_NS}content") or "")
        pub = entry.findtext(f"{ATOM_NS}published") or entry.findtext(f"{ATOM_NS}updated")
        published_at = _parse_datetime(pub)
        author_el = entry.find(f"{ATOM_NS}author")
        author = author_el.findtext(f"{ATOM_NS}name") if author_el is not None else None
        items.append(_to_item(feed_url, title, url, summary, published_at, author))
    return items


def _parse_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        try:
            # Handle common Atom format like 2026-02-21T07:00:00Z
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            return None


def _to_item(
    feed_url: str,
    title: str,
    url: str,
    desc: str,
    published_at: datetime | None,
    author: str | None,
) -> Item:
    digest = hashlib.sha256((url or title).encode("utf-8")).hexdigest()
    return Item(
        id=digest[:16],
        url=url,
        title=title,
        source=feed_url,
        author=author,
        published_at=published_at,
        type="article",
        raw_text=desc,
        description=desc,
        hash=digest,
    )
