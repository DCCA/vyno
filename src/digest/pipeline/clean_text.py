from __future__ import annotations

import re

URL_RE = re.compile(r"https?://\S+")
HASHTAG_LINE_RE = re.compile(r"^(?:\s*#[A-Za-z0-9_\-]+\s*)+$")

BLOCK_MARKERS = [
    "sources:",
    "our patreon",
    "patreon.com",
    "support us",
    "check out",
    "sign up",
    "sponsor",
]


def clean_youtube_text(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    out: list[str] = []
    seen_urls: set[str] = set()
    skipping_sources = False

    for line in lines:
        lower = line.lower()

        if lower.startswith("sources:"):
            skipping_sources = True
            continue

        if skipping_sources:
            if URL_RE.search(line):
                continue
            skipping_sources = False

        if HASHTAG_LINE_RE.match(line):
            continue

        if any(marker in lower for marker in BLOCK_MARKERS):
            # Keep line only if it also carries technical signal.
            if not _has_technical_signal(lower):
                continue

        # Deduplicate repeated URLs in-line.
        urls = URL_RE.findall(line)
        if urls:
            kept_urls: list[str] = []
            for u in urls:
                if u not in seen_urls:
                    seen_urls.add(u)
                    kept_urls.append(u)
            if not kept_urls:
                line = URL_RE.sub("", line).strip()
            else:
                line = URL_RE.sub("", line).strip()
                if line:
                    line = f"{line} {' '.join(kept_urls)}"
                else:
                    line = " ".join(kept_urls)

        line = _strip_emojis(line)
        line = " ".join(line.split())
        if line:
            out.append(line)

    cleaned = "\n".join(out).strip()
    # Hard cap to avoid giant dumps reaching summarization.
    return cleaned[:2400]


def _has_technical_signal(text: str) -> bool:
    keywords = [
        "paper",
        "benchmark",
        "model",
        "render",
        "shader",
        "cuda",
        "agent",
        "llm",
        "research",
        "method",
        "realtime",
        "real-time",
    ]
    return any(k in text for k in keywords)


def _strip_emojis(text: str) -> str:
    # Conservative emoji removal for common pictographs.
    return re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", "", text)
