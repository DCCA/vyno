from __future__ import annotations

import hashlib
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

from digest.models import Item

TAG_RE = re.compile(r"<[^>]+>")
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def _strip_html(text: str) -> str:
    return TAG_RE.sub(" ", text or "").strip()


def fetch_rss_items(feed_urls: list[str], timeout: int = 15, retries: int = 2) -> list[Item]:
    items: list[Item] = []
    for feed_url in feed_urls:
        content = _fetch_with_retry(feed_url, timeout=timeout, retries=retries)
        items.extend(parse_feed_items(feed_url, content))
    return items


def _fetch_with_retry(feed_url: str, timeout: int, retries: int) -> bytes:
    last_err: Exception | None = None
    for _ in range(retries + 1):
        req = urllib.request.Request(
            feed_url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; ai-digest/1.0; +https://example.local)",
                "Accept": "application/rss+xml, application/atom+xml, application/rdf+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            # Retry only for transient server-side failures.
            if exc.code not in {429, 500, 502, 503, 504}:
                raise
            last_err = exc
        except urllib.error.URLError as exc:
            last_err = exc
    if last_err is not None:
        raise last_err
    raise RuntimeError(f"Failed to fetch feed: {feed_url}")


def parse_feed_items(feed_url: str, content: bytes) -> list[Item]:
    root = ET.fromstring(content)
    root_name = _local_name(root.tag)
    if root_name == "rss":
        return _parse_rss_channel(feed_url, root)
    if root_name == "feed":
        return _parse_atom_feed(feed_url, root)
    if root_name == "RDF":
        return _parse_rdf_feed(feed_url, root)
    return _parse_generic_feed(feed_url, root)


def _parse_rss_channel(feed_url: str, root: ET.Element) -> list[Item]:
    channel = root.find("channel")
    if channel is None:
        return []
    items: list[Item] = []
    for entry in channel.findall("item"):
        title = (_first_text(entry, ["title"]) or "Untitled").strip()
        url = (_first_text(entry, ["link"]) or "").strip()
        desc = _strip_html(_first_text(entry, ["description"]) or "")
        pub = _first_text(entry, ["pubDate", "date"]) or ""
        published_at = _parse_datetime(pub)
        author = _first_text(entry, ["author", "creator"]) or None
        items.append(_to_item(feed_url, title, url, desc, published_at, author))
    return items


def _parse_atom_feed(feed_url: str, root: ET.Element) -> list[Item]:
    items: list[Item] = []
    entries = [e for e in root if _local_name(e.tag) == "entry"]
    for entry in entries:
        title = (_first_text(entry, ["title"]) or "Untitled").strip()
        url = _atom_link(entry)
        summary = _strip_html(_first_text(entry, ["summary", "content", "description"]) or "")
        pub = _first_text(entry, ["published", "updated", "pubDate"]) or ""
        published_at = _parse_datetime(pub)
        author = _atom_author(entry)
        items.append(_to_item(feed_url, title, url, summary, published_at, author))
    return items


def _parse_rdf_feed(feed_url: str, root: ET.Element) -> list[Item]:
    items: list[Item] = []
    entries = [e for e in root if _local_name(e.tag) == "item"]
    for entry in entries:
        title = (_first_text(entry, ["title"]) or "Untitled").strip()
        url = (_first_text(entry, ["link"]) or "").strip()
        desc = _strip_html(_first_text(entry, ["description"]) or "")
        pub = _first_text(entry, ["date", "pubDate", "issued"]) or ""
        published_at = _parse_datetime(pub)
        author = _first_text(entry, ["creator", "author"]) or None
        items.append(_to_item(feed_url, title, url, desc, published_at, author))
    return items


def _parse_generic_feed(feed_url: str, root: ET.Element) -> list[Item]:
    items: list[Item] = []
    for entry in root.iter():
        if _local_name(entry.tag) not in {"item", "entry"}:
            continue
        title = (_first_text(entry, ["title"]) or "Untitled").strip()
        url = (_first_text(entry, ["link"]) or "").strip()
        if not url:
            for child in entry:
                if _local_name(child.tag) == "link":
                    href = child.attrib.get("href", "").strip()
                    if href:
                        url = href
                        break
        desc = _strip_html(_first_text(entry, ["description", "summary", "content"]) or "")
        pub = _first_text(entry, ["pubDate", "published", "updated", "date"]) or ""
        published_at = _parse_datetime(pub)
        author = _first_text(entry, ["author", "creator", "name"]) or None
        items.append(_to_item(feed_url, title, url, desc, published_at, author))
    return items


def _first_text(node: ET.Element, names: list[str]) -> str | None:
    for child in node.iter():
        if _local_name(child.tag) in names and child.text:
            value = child.text.strip()
            if value:
                return value
    return None


def _atom_link(entry: ET.Element) -> str:
    candidate = ""
    for child in entry:
        if _local_name(child.tag) != "link":
            continue
        href = (child.attrib.get("href") or "").strip()
        rel = (child.attrib.get("rel") or "alternate").strip().lower()
        if not href:
            continue
        if rel == "alternate":
            return href
        if not candidate:
            candidate = href
    return candidate


def _atom_author(entry: ET.Element) -> str | None:
    for child in entry:
        if _local_name(child.tag) != "author":
            continue
        for sub in child:
            if _local_name(sub.tag) == "name" and sub.text:
                value = sub.text.strip()
                if value:
                    return value
    return None


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    if ":" in tag:
        return tag.split(":", 1)[1]
    return tag


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
