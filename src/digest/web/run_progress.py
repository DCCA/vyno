"""Run-progress, stage-labeling, and timeline-severity helpers for the web
control plane.

These are pure functions extracted from ``digest.web.app``; they operate on
plain stage strings and detail dicts and hold no route or application state.
"""

from __future__ import annotations

from typing import Any

FETCH_STAGES = {
    "fetch_rss",
    "fetch_youtube_channel",
    "fetch_youtube_query",
    "fetch_x_inbox",
    "fetch_x_selectors",
    "fetch_github",
}


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _count_fetch_targets(sources_cfg: Any) -> int:
    total = 0
    total += len(getattr(sources_cfg, "rss_feeds", []) or [])
    total += len(getattr(sources_cfg, "youtube_channels", []) or [])
    total += len(getattr(sources_cfg, "youtube_queries", []) or [])
    total += len(getattr(sources_cfg, "x_authors", []) or [])
    total += len(getattr(sources_cfg, "x_themes", []) or [])
    if str(getattr(sources_cfg, "x_inbox_path", "") or "").strip():
        total += 1
    has_github = any(
        [
            getattr(sources_cfg, "github_repos", None),
            getattr(sources_cfg, "github_topics", None),
            getattr(sources_cfg, "github_search_queries", None),
            getattr(sources_cfg, "github_orgs", None),
        ]
    )
    if has_github:
        total += 1
    return total


def _timeline_event_severity(stage: str, details: dict[str, Any]) -> str:
    if stage == "run_failed":
        return "error"
    status = str(details.get("status", "")).strip().lower()
    if stage == "run_finish":
        if status == "failed":
            return "error"
        if status == "partial":
            return "warn"
    error_text = str(details.get("error", "")).strip()
    if error_text:
        return "error"
    source_errors = _as_int(details.get("source_error_count"))
    summary_errors = _as_int(details.get("summary_error_count"))
    if (source_errors and source_errors > 0) or (summary_errors and summary_errors > 0):
        return "warn"
    return "info"


def _run_stage_label(stage: str) -> str:
    labels = {
        "queued": "Queued",
        "run_start": "Starting",
        "fetch_rss": "Fetching RSS",
        "fetch_youtube_channel": "Fetching YouTube Channels",
        "fetch_youtube_query": "Fetching YouTube Queries",
        "fetch_x_inbox": "Fetching X Inbox",
        "fetch_x_selectors": "Fetching X Selectors",
        "fetch_github": "Fetching GitHub",
        "normalize_filter": "Normalizing",
        "candidate_select": "Selecting Candidates",
        "score_init": "Preparing Scoring",
        "score_progress": "Scoring Items",
        "score": "Scoring Complete",
        "summarize_progress": "Summarizing",
        "summarize": "Summaries Complete",
        "quality_learning": "Applying Quality Priors",
        "quality_judge_start": "Quality Review",
        "quality_judge_result": "Quality Review Complete",
        "quality_repair_applied": "Quality Repair Applied",
        "quality_repair_skipped": "Quality Repair Skipped",
        "quality_learning_update": "Updating Quality Priors",
        "quality_repair": "Quality Repair",
        "deliver_telegram": "Delivering Telegram",
        "deliver_obsidian": "Writing Obsidian",
        "run_finish": "Finished",
        "run_failed": "Failed",
    }
    return labels.get(stage, "Processing")


def _run_stage_detail(stage: str, details: dict[str, Any], *, fallback: str) -> str:
    fetch_done = _as_int(details.get("fetch_done"))
    fetch_total = _as_int(details.get("fetch_total"))
    processed = _as_int(details.get("processed_count"))
    total = _as_int(details.get("total_count"))

    if stage in FETCH_STAGES and fetch_done is not None and fetch_total:
        return f"Collected {fetch_done}/{fetch_total} source targets."
    if stage == "score_progress" and processed is not None and total:
        return f"Scored {processed}/{total} candidates."
    if stage == "summarize_progress" and processed is not None and total:
        fallback_count = _as_int(details.get("fallback_count"))
        if fallback_count and fallback_count > 0:
            return (
                f"Summarized {processed}/{total} items "
                f"({fallback_count} fallback summaries)."
            )
        return f"Summarized {processed}/{total} items."
    if stage == "deliver_telegram":
        chunk = _as_int(details.get("chunk_index"))
        chunk_total = _as_int(details.get("chunk_count"))
        if chunk is not None and chunk_total:
            return f"Sent Telegram message chunk {chunk}/{chunk_total}."
    if stage == "run_finish":
        status = str(details.get("status", "")).strip()
        if status:
            return f"Run completed with status: {status}."
        return "Run completed."
    if stage == "run_failed":
        error = str(details.get("error", "")).strip()
        if error:
            return f"Run failed: {error}"
        return "Run failed before completion."
    return fallback


def _estimate_run_progress_percent(
    stage: str,
    *,
    details: dict[str, Any],
    fetch_done: int,
    fetch_total: int,
) -> float | None:
    if stage == "queued":
        return 1.0
    if stage == "run_start":
        return 3.0
    if stage in FETCH_STAGES:
        if fetch_total > 0:
            return 5.0 + 30.0 * (max(0, min(fetch_done, fetch_total)) / fetch_total)
        return 15.0
    if stage == "normalize_filter":
        return 38.0
    if stage == "candidate_select":
        return 42.0
    if stage == "score_init":
        return 46.0
    if stage == "score_progress":
        processed = _as_int(details.get("processed_count"))
        total = _as_int(details.get("total_count"))
        if processed is not None and total and total > 0:
            frac = max(0.0, min(1.0, processed / total))
            return 46.0 + 24.0 * frac
        return 58.0
    if stage == "score":
        return 70.0
    if stage == "summarize_progress":
        processed = _as_int(details.get("processed_count"))
        total = _as_int(details.get("total_count"))
        if processed is not None and total and total > 0:
            frac = max(0.0, min(1.0, processed / total))
            return 70.0 + 20.0 * frac
        return 82.0
    if stage == "summarize":
        return 90.0
    if stage.startswith("quality_"):
        if stage == "quality_judge_start":
            return 92.0
        if stage in {
            "quality_judge_result",
            "quality_repair_applied",
            "quality_repair_skipped",
            "quality_learning_update",
            "quality_repair",
            "quality_learning",
        }:
            return 94.0
    if stage == "deliver_telegram":
        chunk = _as_int(details.get("chunk_index"))
        chunk_total = _as_int(details.get("chunk_count"))
        if chunk is not None and chunk_total and chunk_total > 0:
            frac = max(0.0, min(1.0, chunk / chunk_total))
            return 94.0 + 3.0 * frac
        return 95.0
    if stage == "deliver_obsidian":
        return 98.0
    if stage in {"run_finish", "run_failed"}:
        return 100.0
    return None
