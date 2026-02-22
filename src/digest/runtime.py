from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from digest.config import ProfileConfig, SourceConfig
from digest.connectors.rss import fetch_rss_items
from digest.connectors.youtube import fetch_youtube_items
from digest.delivery.obsidian import render_obsidian_note, write_obsidian_note
from digest.delivery.telegram import render_telegram_message, send_telegram_message
from digest.models import Item, RunReport, ScoredItem
from digest.pipeline.dedupe import dedupe_and_cluster
from digest.pipeline.normalize import normalize_items
from digest.pipeline.scoring import score_items
from digest.pipeline.selection import select_digest_sections
from digest.pipeline.summarize import FallbackSummarizer
from digest.storage.sqlite_store import SQLiteStore
from digest.summarizers.extractive import ExtractiveSummarizer
from digest.summarizers.responses_api import ResponsesAPISummarizer


def run_digest(sources: SourceConfig, profile: ProfileConfig, store: SQLiteStore) -> RunReport:
    run_id = uuid.uuid4().hex[:12]
    now = datetime.now(tz=timezone.utc)
    window_start = store.last_completed_window_end() or (now - timedelta(hours=24)).isoformat()
    window_end = now.isoformat()
    store.start_run(run_id, window_start, window_end)

    source_errors: list[str] = []
    summary_errors: list[str] = []

    raw_items = []
    for feed_url in sources.rss_feeds:
        try:
            raw_items.extend(fetch_rss_items([feed_url]))
        except Exception as exc:
            source_errors.append(f"rss:{feed_url}: {exc}")

    for channel_id in sources.youtube_channels:
        try:
            raw_items.extend(fetch_youtube_items([channel_id], []))
        except Exception as exc:
            source_errors.append(f"youtube:channel:{channel_id}: {exc}")

    for query in sources.youtube_queries:
        try:
            raw_items.extend(fetch_youtube_items([], [query]))
        except Exception as exc:
            source_errors.append(f"youtube:query:{query}: {exc}")

    normalized = normalize_items(raw_items)
    unique_items = dedupe_and_cluster(normalized)
    unique_items = _filter_window(unique_items, window_start)

    seen = store.seen_keys()
    unseen_items = [i for i in unique_items if (i.url or i.hash) not in seen]

    scores = score_items(unseen_items, profile)
    score_map = {s.item_id: s for s in scores}
    scored_items = [ScoredItem(item=i, score=score_map[i.id]) for i in unseen_items if i.id in score_map]

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

    sections = select_digest_sections(scored_items)
    # Keep note naming aligned with run window timestamps (UTC) to avoid
    # local-time drift where repeated runs overwrite the previous-day note.
    date_str = now.date().isoformat()

    telegram_message = render_telegram_message(date_str, sections)
    note = render_obsidian_note(date_str, sections, source_count=len(unseen_items))

    status = "success"
    if source_errors or summary_errors:
        status = "partial"
    if not raw_items and source_errors:
        status = "failed"

    if profile.output.telegram_bot_token and profile.output.telegram_chat_id:
        try:
            send_telegram_message(profile.output.telegram_bot_token, profile.output.telegram_chat_id, telegram_message)
        except Exception as exc:
            source_errors.append(f"telegram: {exc}")
            status = "partial"

    if profile.output.obsidian_vault_path:
        try:
            write_obsidian_note(profile.output.obsidian_vault_path, profile.output.obsidian_folder, date_str, note)
        except Exception as exc:
            source_errors.append(f"obsidian: {exc}")
            status = "partial"

    store.upsert_items(unseen_items)
    store.insert_scores(run_id, scores)
    store.mark_seen([i.url or i.hash for i in unseen_items])
    store.finish_run(run_id, status, source_errors, summary_errors)

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
