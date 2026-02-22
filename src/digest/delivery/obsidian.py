from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

from digest.models import DigestSections


TAG_CLEAN_RE = re.compile(r"[^a-z0-9-]+")


def _normalize_tag(value: str) -> str:
    raw = (value or "").strip().lower().replace(" ", "-").replace("_", "-")
    raw = TAG_CLEAN_RE.sub("-", raw)
    raw = re.sub(r"-{2,}", "-", raw).strip("-")
    return raw


def _render_tags(tags: list[str]) -> str:
    normalized = [_normalize_tag(t) for t in tags]
    normalized = [t for t in normalized if t]
    return ", ".join(dict.fromkeys(normalized))


def render_obsidian_note(
    date_str: str,
    sections: DigestSections,
    source_count: int,
    *,
    run_id: str = "",
    generated_at_utc: str = "",
) -> str:
    doc_tags = ["ai", "digest"]
    lines = [
        "---",
        f"date: {date_str}",
        f"generated_at_utc: {generated_at_utc}",
        f"run_id: {run_id}",
        f"source_count: {source_count}",
        f"tags: [{', '.join(doc_tags)}]",
        "---",
        "",
        f"# AI Digest - {date_str}",
        "",
        "## Must-read",
    ]
    for idx, item in enumerate(sections.must_read, start=1):
        lines.append(f"> [!summary] {idx}. [{item.item.title}]({item.item.url})")
        if item.score.tags:
            lines.append(f"> Tags: {_render_tags(item.score.tags)}")
        if item.summary:
            lines.append(f"> TL;DR: {item.summary.tldr}")
            lines.append(f"> Why it matters: {item.summary.why_it_matters}")
        lines.append(">")

    lines.extend(["", "## Skim"])
    for item in sections.skim:
        line = f"- [{item.item.title}]({item.item.url})"
        if item.score.tags:
            line += f" — tags: {_render_tags(item.score.tags)}"
        lines.append(line)

    lines.extend(["", "## Videos"])
    for item in sections.videos:
        line = f"- [{item.item.title}]({item.item.url})"
        if item.score.tags:
            line += f" — tags: {_render_tags(item.score.tags)}"
        lines.append(line)

    return "\n".join(lines).strip() + "\n"


def build_obsidian_note_path(
    vault_path: str,
    folder: str,
    naming: str,
    run_dt_utc: datetime,
    run_id: str,
) -> Path:
    target_dir = Path(vault_path) / folder
    date_str = run_dt_utc.date().isoformat()
    if naming == "daily":
        return target_dir / f"{date_str}.md"
    time_part = run_dt_utc.strftime("%H%M%S")
    safe_run = "".join(c for c in run_id if c.isalnum())[:12] or "run"
    return target_dir / date_str / f"{time_part}-{safe_run}.md"


def write_obsidian_note(
    vault_path: str,
    folder: str,
    date_str: str,
    content: str,
    *,
    naming: str = "timestamped",
    run_id: str = "",
    run_dt_utc: datetime | None = None,
) -> Path:
    if run_dt_utc is None:
        run_dt_utc = datetime.now(timezone.utc)
    out_path = build_obsidian_note_path(vault_path, folder, naming, run_dt_utc, run_id)
    target_dir = out_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    temp_path = out_path.with_suffix(".md.tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(out_path)
    return out_path
