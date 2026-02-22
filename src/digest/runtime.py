from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
import logging
import os
from pathlib import Path

from digest.config import ProfileConfig, SourceConfig
from digest.connectors.github import fetch_github_items, normalize_github_org
from digest.connectors.rss import fetch_rss_items
from digest.connectors.x_inbox import fetch_x_inbox_items
from digest.connectors.youtube import fetch_youtube_items
from digest.delivery.obsidian import render_obsidian_note, write_obsidian_note
from digest.delivery.telegram import render_telegram_messages, send_telegram_message
from digest.models import Item, RunReport, ScoredItem
from digest.pipeline.dedupe import dedupe_and_cluster
from digest.pipeline.normalize import normalize_items
from digest.pipeline.scoring import is_blocked, score_item
from digest.pipeline.selection import select_digest_sections
from digest.pipeline.summarize import FallbackSummarizer
from digest.storage.sqlite_store import SQLiteStore
from digest.logging_utils import get_run_logger, log_event
from digest.summarizers.extractive import ExtractiveSummarizer
from digest.summarizers.responses_api import ResponsesAPISummarizer
from digest.scorers.agent import ResponsesAPIScorerTagger


def run_digest(
    sources: SourceConfig,
    profile: ProfileConfig,
    store: SQLiteStore,
    *,
    use_last_completed_window: bool = True,
    only_new: bool = True,
    logger: logging.Logger | logging.LoggerAdapter | None = None,
) -> RunReport:
    run_id = uuid.uuid4().hex[:12]
    run_logger = logger or get_run_logger(run_id)
    now = datetime.now(tz=timezone.utc)
    window_start = (now - timedelta(hours=24)).isoformat()
    if use_last_completed_window:
        window_start = store.last_completed_window_end() or window_start
    window_end = now.isoformat()
    log_event(
        run_logger,
        "info",
        "run_start",
        "Digest run started",
        window_start=window_start,
        window_end=window_end,
        use_last_completed_window=use_last_completed_window,
        only_new=only_new,
    )
    store.start_run(run_id, window_start, window_end)

    source_errors: list[str] = []
    summary_errors: list[str] = []

    raw_items = []
    for feed_url in sources.rss_feeds:
        try:
            fetched = fetch_rss_items([feed_url])
            raw_items.extend(fetched)
            log_event(run_logger, "info", "fetch_rss", "Fetched RSS source", source=feed_url, item_count=len(fetched))
        except Exception as exc:
            source_errors.append(f"rss:{feed_url}: {exc}")
            log_event(run_logger, "error", "fetch_rss", "RSS source fetch failed", source=feed_url, error=str(exc))

    for channel_id in sources.youtube_channels:
        try:
            fetched = fetch_youtube_items([channel_id], [])
            raw_items.extend(fetched)
            log_event(
                run_logger,
                "info",
                "fetch_youtube_channel",
                "Fetched YouTube channel source",
                channel_id=channel_id,
                item_count=len(fetched),
            )
        except Exception as exc:
            source_errors.append(f"youtube:channel:{channel_id}: {exc}")
            log_event(
                run_logger,
                "error",
                "fetch_youtube_channel",
                "YouTube channel fetch failed",
                channel_id=channel_id,
                error=str(exc),
            )

    for query in sources.youtube_queries:
        try:
            fetched = fetch_youtube_items([], [query])
            raw_items.extend(fetched)
            log_event(
                run_logger,
                "info",
                "fetch_youtube_query",
                "Fetched YouTube query source",
                query=query,
                item_count=len(fetched),
            )
        except Exception as exc:
            source_errors.append(f"youtube:query:{query}: {exc}")
            log_event(
                run_logger,
                "error",
                "fetch_youtube_query",
                "YouTube query fetch failed",
                query=query,
                error=str(exc),
            )

    if sources.x_inbox_path:
        try:
            fetched = fetch_x_inbox_items(sources.x_inbox_path)
            raw_items.extend(fetched)
            log_event(
                run_logger,
                "info",
                "fetch_x_inbox",
                "Fetched X inbox items",
                inbox_path=sources.x_inbox_path,
                item_count=len(fetched),
            )
        except Exception as exc:
            source_errors.append(f"x_inbox:{sources.x_inbox_path}: {exc}")
            log_event(
                run_logger,
                "error",
                "fetch_x_inbox",
                "X inbox fetch failed",
                inbox_path=sources.x_inbox_path,
                error=str(exc),
            )

    if sources.github_repos or sources.github_topics or sources.github_search_queries or sources.github_orgs:
        try:
            gh_token = os.getenv("GITHUB_TOKEN", "").strip()
            github_orgs = [normalize_github_org(v) for v in sources.github_orgs]
            github_orgs = [v for v in github_orgs if v]
            fetched = fetch_github_items(
                sources.github_repos,
                sources.github_topics,
                sources.github_search_queries,
                orgs=github_orgs,
                token=gh_token,
                org_options={
                    "min_stars": profile.github_min_stars,
                    "include_forks": profile.github_include_forks,
                    "include_archived": profile.github_include_archived,
                    "max_repos_per_org": profile.github_max_repos_per_org,
                    "max_items_per_org": profile.github_max_items_per_org,
                },
            )
            raw_items.extend(fetched)
            log_event(
                run_logger,
                "info",
                "fetch_github",
                "Fetched GitHub items",
                repo_count=len(sources.github_repos),
                topic_count=len(sources.github_topics),
                query_count=len(sources.github_search_queries),
                org_count=len(github_orgs),
                item_count=len(fetched),
            )
        except Exception as exc:
            source_errors.append(f"github: {exc}")
            log_event(run_logger, "error", "fetch_github", "GitHub fetch failed", error=str(exc))

    normalized = normalize_items(raw_items)
    unique_items = dedupe_and_cluster(normalized)
    unique_items = _filter_window(unique_items, window_start)
    log_event(
        run_logger,
        "info",
        "normalize_filter",
        "Normalized and filtered candidates",
        raw_count=len(raw_items),
        unique_count=len(unique_items),
    )

    seen = store.seen_keys()
    candidate_items = unique_items
    if only_new:
        candidate_items = [i for i in unique_items if (i.url or i.hash) not in seen]
        # Keep delivery non-empty for manual/interactive usage when window has content
        # but all items were already seen in previous runs.
        if not candidate_items and unique_items:
            candidate_items = unique_items
    log_event(
        run_logger,
        "info",
        "candidate_select",
        "Selected candidate items",
        seen_count=len(seen),
        candidate_count=len(candidate_items),
    )

    scores = []
    agent_scorer = None
    if profile.agent_scoring_enabled:
        try:
            agent_scorer = ResponsesAPIScorerTagger(model=profile.openai_model)
            log_event(run_logger, "info", "score_init", "Agent scorer initialized", model=profile.openai_model)
        except Exception as exc:
            log_event(run_logger, "error", "score_init", "Agent scorer unavailable, using rules fallback", error=str(exc))

    for item in candidate_items:
        if is_blocked(item, profile):
            continue
        if agent_scorer is not None:
            try:
                scores.append(agent_scorer.score_and_tag(item))
                continue
            except Exception as exc:
                log_event(
                    run_logger,
                    "error",
                    "score_agent",
                    "Agent scoring failed, using rules fallback",
                    item_id=item.id,
                    error=str(exc),
                )
        scores.append(score_item(item, profile))
    score_map = {s.item_id: s for s in scores}
    scored_items = [ScoredItem(item=i, score=score_map[i.id]) for i in candidate_items if i.id in score_map]
    log_event(run_logger, "info", "score", "Scored candidate items", score_count=len(scores), scored_item_count=len(scored_items))

    primary = ExtractiveSummarizer()
    if profile.llm_enabled:
        try:
            primary = ResponsesAPISummarizer(model=profile.openai_model)
        except Exception as exc:
            summary_errors.append(f"llm_init: {exc}")
            primary = ExtractiveSummarizer()

    summarizer = FallbackSummarizer(primary=primary, fallback=ExtractiveSummarizer())
    for scored in scored_items:
        summary, err = summarizer.summarize(scored.item)
        scored.summary = summary
        if err:
            summary_errors.append(f"{scored.item.id}: {err}")
            log_event(
                run_logger,
                "error",
                "summarize",
                "Summary fallback used",
                item_id=scored.item.id,
                error=err,
            )

    sections = select_digest_sections(scored_items)
    # Keep note naming aligned with run window timestamps (UTC) to avoid
    # local-time drift where repeated runs overwrite the previous-day note.
    date_str = now.date().isoformat()

    telegram_messages = render_telegram_messages(
        date_str,
        sections,
        render_mode=profile.output.render_mode,
    )
    _write_latest_telegram_artifact(run_id, telegram_messages)
    note = render_obsidian_note(
        date_str,
        sections,
        source_count=len(candidate_items),
        run_id=run_id,
        generated_at_utc=now.isoformat(),
        render_mode=profile.output.render_mode,
    )

    status = "success"
    if source_errors or summary_errors:
        status = "partial"
    if not raw_items and source_errors:
        status = "failed"

    if profile.output.telegram_bot_token and profile.output.telegram_chat_id:
        try:
            for idx, chunk in enumerate(telegram_messages, start=1):
                send_telegram_message(profile.output.telegram_bot_token, profile.output.telegram_chat_id, chunk)
                log_event(
                    run_logger,
                    "info",
                    "deliver_telegram",
                    "Telegram message sent",
                    chunk_index=idx,
                    chunk_count=len(telegram_messages),
                )
        except Exception as exc:
            source_errors.append(f"telegram: {exc}")
            status = "partial"
            log_event(run_logger, "error", "deliver_telegram", "Telegram delivery failed", error=str(exc))

    if profile.output.obsidian_vault_path:
        try:
            out_path = write_obsidian_note(
                profile.output.obsidian_vault_path,
                profile.output.obsidian_folder,
                date_str,
                note,
                naming=profile.output.obsidian_naming,
                run_id=run_id,
                run_dt_utc=now,
            )
            log_event(run_logger, "info", "deliver_obsidian", "Obsidian note written", path=str(out_path))
        except Exception as exc:
            source_errors.append(f"obsidian: {exc}")
            status = "partial"
            log_event(run_logger, "error", "deliver_obsidian", "Obsidian write failed", error=str(exc))

    store.upsert_items(candidate_items)
    store.insert_scores(run_id, scores)
    store.mark_seen([i.url or i.hash for i in candidate_items])
    store.finish_run(run_id, status, source_errors, summary_errors)
    log_event(
        run_logger,
        "info",
        "run_finish",
        "Digest run finished",
        status=status,
        source_error_count=len(source_errors),
        summary_error_count=len(summary_errors),
        final_item_count=len(scored_items),
    )

    return RunReport(run_id=run_id, status=status, source_errors=source_errors, summary_errors=summary_errors)


def _filter_window(items: list[Item], window_start_iso: str) -> list[Item]:
    start = datetime.fromisoformat(window_start_iso)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    filtered = []
    for item in items:
        published = item.published_at
        if published is not None and published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        if published is None or published >= start:
            filtered.append(item)
    return filtered


def _write_latest_telegram_artifact(run_id: str, messages: list[str]) -> None:
    path = Path(".runtime/last_telegram_messages.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "chunk_count": len(messages),
        "messages": messages,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
