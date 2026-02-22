from __future__ import annotations

from pathlib import Path

from digest.models import DigestSections


def render_obsidian_note(date_str: str, sections: DigestSections, source_count: int) -> str:
    lines = [
        "---",
        f"date: {date_str}",
        "tags: [ai, digest]",
        f"source_count: {source_count}",
        "---",
        "",
        f"# AI Digest - {date_str}",
        "",
        "## Must-read",
    ]
    for idx, item in enumerate(sections.must_read, start=1):
        lines.append(f"{idx}. **{item.item.title}**")
        lines.append(f"   - Link: {item.item.url}")
        if item.summary:
            lines.append(f"   - TL;DR: {item.summary.tldr}")
            lines.append(f"   - Why it matters: {item.summary.why_it_matters}")

    lines.extend(["", "## Skim"])
    for item in sections.skim:
        lines.append(f"- [{item.item.title}]({item.item.url})")

    lines.extend(["", "## Videos"])
    for item in sections.videos:
        lines.append(f"- [{item.item.title}]({item.item.url})")

    return "\n".join(lines).strip() + "\n"


def write_obsidian_note(vault_path: str, folder: str, date_str: str, content: str) -> Path:
    target_dir = Path(vault_path) / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"{date_str}.md"
    temp_path = out_path.with_suffix(".md.tmp")
    temp_path.write_text(content, encoding="utf-8")
    temp_path.replace(out_path)
    return out_path
