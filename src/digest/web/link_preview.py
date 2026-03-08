from __future__ import annotations

from html.parser import HTMLParser
import re
from urllib.parse import urljoin, urlparse
import urllib.request


DEFAULT_PREVIEW_TIMEOUT_SECONDS = 4
MAX_PREVIEW_BYTES = 256 * 1024
PREVIEW_USER_AGENT = "ai-digest/1.0 (+https://example.local)"
WHITESPACE_RE = re.compile(r"\s+")


class _PreviewParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered == "title":
            self.in_title = True
            return
        if lowered != "meta":
            return
        attr_map = {str(key).lower(): str(value or "") for key, value in attrs}
        key = (attr_map.get("property") or attr_map.get("name") or "").strip().lower()
        content = (attr_map.get("content") or "").strip()
        if key and content and key not in self.meta:
            self.meta[key] = content

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title and data:
            self.title_parts.append(data)

    def pick(self, *keys: str) -> str:
        for key in keys:
            value = (self.meta.get(key.lower()) or "").strip()
            if value:
                return value
        return ""

    @property
    def title(self) -> str:
        joined = " ".join(self.title_parts)
        return WHITESPACE_RE.sub(" ", joined).strip()


def _clean_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", (value or "").strip())


def _host_label(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().replace("www.", "")


def fetch_link_preview_metadata(
    url: str,
    *,
    timeout: int = DEFAULT_PREVIEW_TIMEOUT_SECONDS,
) -> dict[str, str]:
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("preview URL must be a valid http/https URL")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": PREVIEW_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = str(response.geturl() or url)
        content_type = str(response.headers.get("Content-Type", "") or "").lower()
        body = response.read(MAX_PREVIEW_BYTES)

    if content_type and "html" not in content_type:
        raise RuntimeError(f"unsupported preview content type: {content_type}")

    parser = _PreviewParser()
    parser.feed(body.decode("utf-8", errors="ignore"))

    title = _clean_text(parser.pick("og:title", "twitter:title") or parser.title)
    description = _clean_text(
        parser.pick("og:description", "twitter:description", "description")
    )
    image = parser.pick("og:image", "twitter:image")
    image_url = urljoin(final_url, image) if image else ""

    return {
        "url": url,
        "resolved_url": final_url,
        "host": _host_label(final_url),
        "title": title,
        "description": description,
        "image_url": image_url,
        "status": "ready",
        "error": "",
    }
