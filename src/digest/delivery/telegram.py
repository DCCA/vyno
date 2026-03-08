from __future__ import annotations

import html
import json
import re
from typing import Any
import urllib.parse
import urllib.request

from digest.models import DigestSections

NOISE_PHRASE_RE = re.compile(
    r"\b(check out|patreon|sponsor|support us|sign up)\b", re.IGNORECASE
)
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
SPACE_RE = re.compile(r"\s+")


def _clean_text(value: str, *, max_len: int) -> str:
    text = (value or "").strip()
    text = NOISE_PHRASE_RE.sub("", text)
    text = URL_RE.sub("", text)
    text = SPACE_RE.sub(" ", text).strip(" -")
    if len(text) > max_len:
        return text[: max_len - 1].rstrip() + "…"
    return text


def render_telegram_messages(
    date_str: str,
    sections: DigestSections,
    *,
    max_len: int = 4000,
    render_mode: str = "sectioned",
    context: dict[str, Any] | None = None,
) -> list[str]:
    if max_len < 256:
        raise ValueError("max_len must be >= 256")
    blocks = _build_digest_blocks(date_str, sections, context=context)
    return _chunk_blocks(blocks, max_len=max_len)


def render_telegram_message(
    date_str: str,
    sections: DigestSections,
    *,
    context: dict[str, Any] | None = None,
) -> str:
    return "\n\n".join(
        render_telegram_messages(
            date_str,
            sections,
            render_mode="sectioned",
            context=context,
        )
    )


def _build_digest_lines(
    date_str: str,
    sections: DigestSections,
    *,
    context: dict[str, Any] | None,
) -> list[str]:
    return [
        line
        for block in _build_digest_blocks(date_str, sections, context=context)
        for line in block.splitlines()
    ]


def _build_digest_blocks(
    date_str: str,
    sections: DigestSections,
    *,
    context: dict[str, Any] | None,
) -> list[str]:
    blocks = [f"AI Digest - {date_str}"]
    sparse_note = _build_sparse_note(context)
    if sparse_note:
        blocks.append(sparse_note)

    primary_items = _select_primary_items(sections)
    for idx, item in enumerate(primary_items, start=1):
        blocks.append(_render_item_block(idx, item))
    return blocks


def _build_context_lines(context: dict[str, Any] | None) -> list[str]:
    if not context:
        return []
    mode = context.get("mode") if isinstance(context.get("mode"), dict) else {}
    fetched = context.get("fetched") if isinstance(context.get("fetched"), dict) else {}
    pipeline = (
        context.get("pipeline") if isinstance(context.get("pipeline"), dict) else {}
    )
    filtering = (
        context.get("filtering") if isinstance(context.get("filtering"), dict) else {}
    )
    video_funnel = (
        context.get("video_funnel")
        if isinstance(context.get("video_funnel"), dict)
        else {}
    )
    selection = (
        context.get("selection") if isinstance(context.get("selection"), dict) else {}
    )

    only_new = bool(mode.get("only_new", False))
    run_mode = "incremental" if only_new else "manual"
    lines = [
        f"- mode={run_mode}",
        (
            "- fetched "
            f"rss={int(fetched.get('rss_items', 0) or 0)} "
            f"yt={int(fetched.get('youtube_items', 0) or 0)} "
            f"x={int(fetched.get('x_items', 0) or 0)} "
            f"gh={int(fetched.get('github_items', 0) or 0)}"
        ),
        (
            "- candidates "
            f"unique={int(pipeline.get('unique_count', 0) or 0)} "
            f"final={int(pipeline.get('candidate_count', 0) or 0)}"
        ),
        (
            "- filters "
            f"seen={int(pipeline.get('seen_count', 0) or 0)} "
            f"low-impact-issues={int(pipeline.get('github_issue_dropped_low_impact', 0) or 0)}"
        ),
        (
            "- dropped "
            f"dedupe={int(filtering.get('dedupe_dropped', 0) or 0)} "
            f"window={int(filtering.get('window_dropped', 0) or 0)} "
            f"seen={int(filtering.get('seen_dropped', 0) or 0)} "
            f"blocked={int(filtering.get('blocked_dropped', 0) or 0)} "
            f"ranked-out={int(filtering.get('ranking_dropped', 0) or 0)}"
        ),
        (
            "- videos "
            f"fetched={int(video_funnel.get('fetched', 0) or 0)} "
            f"post-window={int(video_funnel.get('post_window', 0) or 0)} "
            f"post-seen={int(video_funnel.get('post_seen', 0) or 0)} "
            f"post-block={int(video_funnel.get('post_block', 0) or 0)} "
            f"selected={int(video_funnel.get('selected', 0) or 0)}"
        ),
        (
            "- selected "
            f"M/S/V={int(selection.get('must_read_count', 0) or 0)}/"
            f"{int(selection.get('skim_count', 0) or 0)}/"
            f"{int(selection.get('video_count', 0) or 0)}"
        ),
    ]
    sparse_note = str(context.get("sparse_note", "")).strip()
    if sparse_note:
        lines.append(f"- {sparse_note}")
    return lines


def _build_sparse_note(context: dict[str, Any] | None) -> str:
    if not context:
        return ""
    sparse_note = _clean_text(str(context.get("sparse_note", "")).strip(), max_len=180)
    if not sparse_note:
        return ""
    return f"<i>{html.escape(sparse_note, quote=True)}</i>"


def _select_primary_items(sections: DigestSections):
    if sections.must_read:
        return list(sections.must_read)
    if sections.skim:
        return list(sections.skim)
    return list(sections.videos)


def _render_item_block(idx: int, scored_item) -> str:
    title = _clean_text(scored_item.item.title, max_len=90) or "Untitled item"
    summary = _best_summary_text(scored_item)
    safe_url = html.escape(scored_item.item.url, quote=True)
    safe_title = html.escape(title, quote=True)
    safe_summary = html.escape(summary, quote=True)
    return (
        f"{idx}. <a href=\"{safe_url}\"><b>{safe_title}</b></a>\n"
        f"{safe_summary}"
    )


def _best_summary_text(scored_item) -> str:
    title = _clean_text(scored_item.item.title, max_len=90)
    candidates: list[str] = []
    summary = scored_item.summary
    if summary:
        candidates.append(summary.tldr or "")
        candidates.extend(summary.key_points or [])
    candidates.append(scored_item.item.description or "")
    candidates.append(scored_item.item.raw_text or "")
    candidates.append(title)

    normalized_title = _normalize_compare_text(title)
    for candidate in candidates:
        cleaned = _clean_text(candidate, max_len=160)
        if not cleaned:
            continue
        if _normalize_compare_text(cleaned) == normalized_title:
            continue
        return cleaned
    return title or "Open item"


def _normalize_compare_text(value: str) -> str:
    lowered = (value or "").strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return SPACE_RE.sub(" ", lowered).strip()


def _chunk_lines(lines: list[str], *, max_len: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        if len(line) > max_len:
            # Keep behavior deterministic even for pathological titles.
            line = line[: max_len - 1] + "…"
        delta = len(line) + (1 if current else 0)
        if current and current_len + delta > max_len:
            chunks.append("\n".join(current).strip())
            current = [line]
            current_len = len(line)
            continue
        current.append(line)
        current_len += delta

    if current:
        chunks.append("\n".join(current).strip())
    return [c for c in chunks if c]


def _chunk_blocks(blocks: list[str], *, max_len: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for block in blocks:
        text = block.strip()
        if not text:
            continue
        if len(text) > max_len:
            lines = text.splitlines()
            truncated = _chunk_lines(lines, max_len=max_len)
            if truncated:
                text = truncated[0]
        separator = 2 if current else 0
        if current and current_len + separator + len(text) > max_len:
            chunks.append("\n\n".join(current).strip())
            current = [text]
            current_len = len(text)
            continue
        current.append(text)
        current_len += separator + len(text)

    if current:
        chunks.append("\n\n".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def send_telegram_message(
    bot_token: str, chat_id: str, message: str, reply_markup: dict | None = None
) -> None:
    if not bot_token or not chat_id:
        raise ValueError("Telegram bot token and chat id are required")
    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": "true",
        "parse_mode": "HTML",
    }
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup, separators=(",", ":"))
    body = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError("Telegram send failed")


def get_telegram_updates(
    bot_token: str, *, offset: int | None = None, timeout: int = 30
) -> list[dict]:
    if not bot_token:
        raise ValueError("Telegram bot token is required")
    query = {"timeout": str(max(1, timeout))}
    if offset is not None:
        query["offset"] = str(offset)
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout + 10) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError("Telegram getUpdates failed")
    rows = result.get("result", [])
    return rows if isinstance(rows, list) else []


def answer_telegram_callback(
    bot_token: str, callback_query_id: str, text: str = ""
) -> None:
    if not bot_token or not callback_query_id:
        raise ValueError("Telegram bot token and callback_query_id are required")
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text[:180]
    body = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError("Telegram answerCallbackQuery failed")
