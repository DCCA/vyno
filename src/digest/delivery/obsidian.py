from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

from digest.delivery.source_buckets import build_source_buckets, top_highlights
from digest.models import DigestSections


TAG_CLEAN_RE = re.compile(r"[^a-z0-9-]+")
NOISE_PHRASE_RE = re.compile(r"\b(check out|patreon|sponsor|support us|sign up)\b", re.IGNORECASE)


def _normalize_tag(value: str) -> str:
    raw = (value or "").strip().lower().replace(" ", "-").replace("_", "-")
    raw = TAG_CLEAN_RE.sub("-", raw)
    raw = re.sub(r"-{2,}", "-", raw).strip("-")
    return raw


def _render_tags(tags: list[str]) -> str:
    normalized = [_normalize_tag(t) for t in tags]
    normalized = [t for t in normalized if t]
    return ", ".join(dict.fromkeys(normalized))


def _clean_text(value: str, *, max_len: int) -> str:
    text = (value or "").strip()
    text = NOISE_PHRASE_RE.sub("", text)
    text = re.sub(r"\s{2,}", " ", text).strip(" -")
    if len(text) > max_len:
        return text[: max_len - 1].rstrip() + "…"
    return text


def render_obsidian_note(
    date_str: str,
    sections: DigestSections,
    source_count: int,
    *,
    run_id: str = "",
    generated_at_utc: str = "",
    render_mode: str = "sectioned",
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
    ]
    if render_mode == "source_segmented":
        lines.extend(_render_source_segmented_sections(sections))
        return "\n".join(lines).strip() + "\n"

    lines.append("## Must-read")
    for idx, item in enumerate(sections.must_read, start=1):
        safe_title = _clean_text(item.item.title, max_len=140)
        lines.append(f"> [!summary] {idx}. [{safe_title}]({item.item.url})")
        if item.score.tags:
            lines.append(f"> Tags: {_render_tags(item.score.tags)}")
        if item.summary:
            lines.append(f"> TL;DR: {_clean_text(item.summary.tldr, max_len=240)}")
            lines.append(f"> Why it matters: {_clean_text(item.summary.why_it_matters, max_len=240)}")
        lines.append(">")

    lines.extend(["", "## Skim"])
    for item in sections.skim:
        safe_title = _clean_text(item.item.title, max_len=140)
        line = f"- [{safe_title}]({item.item.url})"
        if item.score.tags:
            line += f" — tags: {_render_tags(item.score.tags)}"
        lines.append(line)

    lines.extend(["", "## Videos"])
    for item in sections.videos:
        safe_title = _clean_text(item.item.title, max_len=140)
        line = f"- [{safe_title}]({item.item.url})"
        if item.score.tags:
            line += f" — tags: {_render_tags(item.score.tags)}"
        lines.append(line)

    return "\n".join(lines).strip() + "\n"


def _render_source_segmented_sections(sections: DigestSections) -> list[str]:
    lines = ["## Top Highlights"]
    for idx, item in enumerate(top_highlights(sections, limit=3), start=1):
        safe_title = _clean_text(item.item.title, max_len=140)
        lines.append(f"{idx}. [{safe_title}]({item.item.url})")
        if item.summary:
            lines.append(f"   - TL;DR: {_clean_text(item.summary.tldr, max_len=240)}")
        if item.score.tags:
            lines.append(f"   - Tags: {_render_tags(item.score.tags)}")

    buckets = build_source_buckets(sections, per_bucket_limit=8)
    for bucket, rows in buckets.items():
        lines.extend(["", f"## {bucket}"])
        for item in rows:
            safe_title = _clean_text(item.item.title, max_len=140)
            line = f"- [{safe_title}]({item.item.url})"
            if item.score.tags:
                line += f" — tags: {_render_tags(item.score.tags)}"
            lines.append(line)
    return lines


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
