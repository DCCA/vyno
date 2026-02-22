from __future__ import annotations

import json
import urllib.parse
import urllib.request

from digest.models import DigestSections


def render_telegram_message(date_str: str, sections: DigestSections) -> str:
    lines = [f"AI Digest - {date_str}", "", "Must-read"]
    for idx, item in enumerate(sections.must_read, start=1):
        summary = item.summary.tldr if item.summary else item.item.title
        lines.append(f"{idx}. {item.item.title} - {summary} ({item.item.url})")

    lines.extend(["", "Skim"])
    for item in sections.skim:
        lines.append(f"- {item.item.title} ({item.item.url})")

    lines.extend(["", "Videos"])
    for item in sections.videos:
        takeaway = item.summary.key_points[0] if item.summary and item.summary.key_points else item.item.title
        lines.append(f"- {item.item.title} - {takeaway} ({item.item.url})")

    if sections.themes:
        lines.extend(["", "Themes"])
        for theme in sections.themes:
            lines.append(f"- {theme}")

    return "\n".join(lines).strip()


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> None:
    if not bot_token or not chat_id:
        raise ValueError("Telegram bot token and chat id are required")
    payload = {"chat_id": chat_id, "text": message}
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
