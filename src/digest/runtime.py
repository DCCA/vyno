from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
import logging
import os
from pathlib import Path
from typing import Any, Callable

from digest.config import ProfileConfig, SourceConfig
from digest.connectors.github import fetch_github_items, normalize_github_org
from digest.connectors.rss import fetch_rss_items
from digest.connectors.x_inbox import fetch_x_inbox_items
from digest.connectors.youtube import fetch_youtube_items
from digest.delivery.obsidian import render_obsidian_note, write_obsidian_note
from digest.delivery.telegram import render_telegram_messages, send_telegram_message
from digest.models import Item, RunReport, ScoredItem
from digest.pipeline.dedupe import dedupe_and_cluster
from digest.pipeline.github_issue_impact import evaluate_github_issue_impact
from digest.pipeline.normalize import normalize_items
from digest.pipeline.scoring import is_blocked, score_item
from digest.pipeline.selection import rank_scored_items, select_digest_sections
from digest.pipeline.summarize import FallbackSummarizer
from digest.quality.online_repair import (
    ResponsesAPIQualityRepair,
    build_rank_overrides,
    compute_repair_feature_deltas,
    item_features,
    rebuild_sections_with_repair,
)
from digest.storage.sqlite_store import SQLiteStore
from digest.logging_utils import get_run_logger, log_event
from digest.summarizers.extractive import ExtractiveSummarizer
from digest.summarizers.responses_api import ResponsesAPISummarizer
from digest.scorers.agent import ResponsesAPIScorerTagger


ProgressCallback = Callable[[dict[str, Any]], None]


def run_digest(
    sources: SourceConfig,
    profile: ProfileConfig,
    store: SQLiteStore,
    *,
    use_last_completed_window: bool = True,
    only_new: bool = True,
    allow_seen_fallback: bool = True,
    preview_mode: bool = False,
    logger: logging.Logger | logging.LoggerAdapter | None = None,
    progress_cb: ProgressCallback | None = None,
) -> RunReport:
    run_id = uuid.uuid4().hex[:12]
    run_logger = logger or get_run_logger(run_id)
    now = datetime.now(tz=timezone.utc)
    run_started_at = now

    def emit_progress(stage: str, message: str, **fields: Any) -> None:
        if progress_cb is None:
            return
        payload: dict[str, Any] = {
            "run_id": run_id,
            "stage": stage,
            "message": message,
            "elapsed_s": round(
                (datetime.now(tz=timezone.utc) - run_started_at).total_seconds(),
                1,
            ),
        }
        payload.update(fields)
        try:
            progress_cb(payload)
        except Exception:
            return

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
        preview_mode=preview_mode,
    )
    store.start_run(run_id, window_start, window_end)
    emit_progress(
        "run_start",
        "Digest run started",
        window_start=window_start,
        window_end=window_end,
        preview_mode=preview_mode,
    )

    source_errors: list[str] = []
    summary_errors: list[str] = []

    raw_items = []
    for feed_url in sources.rss_feeds:
        try:
            fetched = fetch_rss_items([feed_url])
            raw_items.extend(fetched)
            log_event(
                run_logger,
                "info",
                "fetch_rss",
                "Fetched RSS source",
                source=feed_url,
                item_count=len(fetched),
            )
            emit_progress(
                "fetch_rss",
                "Fetched RSS source",
                source=feed_url,
                item_count=len(fetched),
            )
        except Exception as exc:
            source_errors.append(f"rss:{feed_url}: {exc}")
            log_event(
                run_logger,
                "error",
                "fetch_rss",
                "RSS source fetch failed",
                source=feed_url,
                error=str(exc),
            )
            emit_progress(
                "fetch_rss",
                "RSS source fetch failed",
                source=feed_url,
                error=str(exc),
            )

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
            emit_progress(
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
            emit_progress(
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
            emit_progress(
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
            emit_progress(
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
            emit_progress(
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
            emit_progress(
                "fetch_x_inbox",
                "X inbox fetch failed",
                inbox_path=sources.x_inbox_path,
                error=str(exc),
            )

    if (
        sources.github_repos
        or sources.github_topics
        or sources.github_search_queries
        or sources.github_orgs
    ):
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
                    "repo_max_age_days": profile.github_repo_max_age_days,
                    "activity_max_age_days": profile.github_activity_max_age_days,
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
            emit_progress(
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
            log_event(
                run_logger,
                "error",
                "fetch_github",
                "GitHub fetch failed",
                error=str(exc),
            )
            emit_progress("fetch_github", "GitHub fetch failed", error=str(exc))

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
    emit_progress(
        "normalize_filter",
        "Normalized and filtered candidates",
        raw_count=len(raw_items),
        unique_count=len(unique_items),
    )

    seen = store.seen_keys()
    candidate_items = unique_items
    supplemental_seen_videos = 0
    github_issue_kept_high_impact = 0
    github_issue_dropped_low_impact = 0
    if only_new:
        candidate_items = [i for i in unique_items if (i.url or i.hash) not in seen]
        # Keep delivery non-empty for manual/interactive usage when window has content
        # but all items were already seen in previous runs.
        if allow_seen_fallback and not candidate_items and unique_items:
            candidate_items = unique_items
        elif not allow_seen_fallback and candidate_items:
            has_video = any(i.type == "video" for i in candidate_items)
            if not has_video:
                existing_ids = {i.id for i in candidate_items}
                seen_videos = [
                    i
                    for i in unique_items
                    if i.type == "video"
                    and (i.url or i.hash) in seen
                    and i.id not in existing_ids
                ]
                seen_videos.sort(
                    key=lambda i: (
                        i.published_at or datetime.min.replace(tzinfo=timezone.utc)
                    ),
                    reverse=True,
                )
                supplements = seen_videos[:2]
                if supplements:
                    candidate_items.extend(supplements)
                    supplemental_seen_videos = len(supplements)

    filtered_candidates: list[Item] = []
    for item in candidate_items:
        if item.type != "github_issue":
            filtered_candidates.append(item)
            continue
        decision = evaluate_github_issue_impact(item, profile)
        if decision.keep:
            github_issue_kept_high_impact += 1
            filtered_candidates.append(item)
            continue
        github_issue_dropped_low_impact += 1
    candidate_items = filtered_candidates

    log_event(
        run_logger,
        "info",
        "candidate_select",
        "Selected candidate items",
        seen_count=len(seen),
        candidate_count=len(candidate_items),
        supplemental_seen_videos=supplemental_seen_videos,
        github_issue_kept_high_impact=github_issue_kept_high_impact,
        github_issue_dropped_low_impact=github_issue_dropped_low_impact,
    )
    emit_progress(
        "candidate_select",
        "Selected candidate items",
        candidate_count=len(candidate_items),
        seen_count=len(seen),
        supplemental_seen_videos=supplemental_seen_videos,
        github_issue_kept_high_impact=github_issue_kept_high_impact,
        github_issue_dropped_low_impact=github_issue_dropped_low_impact,
    )

    scores = []
    agent_scorer = None
    llm_scored_count = 0
    fallback_scored_count = 0
    policy_fallback_count = 0
    cache_hits = 0
    cache_misses = 0
    fallback_reasons: Counter[str] = Counter()
    max_llm_requests_per_run = max(0, int(profile.max_llm_requests_per_run))
    llm_requests_used = 0
    llm_budget_reported_ops: set[str] = set()

    def reserve_llm_request(operation: str) -> bool:
        nonlocal llm_requests_used
        if llm_requests_used < max_llm_requests_per_run:
            llm_requests_used += 1
            return True
        if operation not in llm_budget_reported_ops:
            llm_budget_reported_ops.add(operation)
            log_event(
                run_logger,
                "info",
                "llm_budget",
                "LLM request budget exhausted",
                operation=operation,
                max_llm_requests_per_run=max_llm_requests_per_run,
                llm_requests_used=llm_requests_used,
            )
            emit_progress(
                "llm_budget",
                "LLM request budget exhausted",
                operation=operation,
                max_llm_requests_per_run=max_llm_requests_per_run,
                llm_requests_used=llm_requests_used,
            )
        return False

    eligible_items = [item for item in candidate_items if not is_blocked(item, profile)]
    rules_scores = {item.id: score_item(item, profile) for item in eligible_items}
    eligible_count = len(eligible_items)

    agent_scope_ids: set[str] = set()
    if profile.agent_scoring_enabled:
        ranked_for_agent = sorted(
            eligible_items,
            key=lambda i: rules_scores[i.id].total,
            reverse=True,
        )
        agent_scope_ids = {
            item.id for item in ranked_for_agent[: profile.max_agent_items_per_run]
        }
        try:
            agent_scorer = ResponsesAPIScorerTagger(model=profile.openai_model)
            log_event(
                run_logger,
                "info",
                "score_init",
                "Agent scorer initialized",
                model=profile.openai_model,
                max_agent_items_per_run=profile.max_agent_items_per_run,
            )
            emit_progress(
                "score_init",
                "Agent scorer initialized",
                model=profile.openai_model,
                max_agent_items_per_run=profile.max_agent_items_per_run,
            )
        except Exception as exc:
            log_event(
                run_logger,
                "error",
                "score_init",
                "Agent scorer unavailable, using rules fallback",
                error=str(exc),
            )
            emit_progress(
                "score_init",
                "Agent scorer unavailable, using rules fallback",
                error=str(exc),
            )

    agent_scope_count = len(agent_scope_ids)
    total_candidates = len(candidate_items)

    def emit_score_progress(processed_count: int) -> None:
        if processed_count <= 0 or total_candidates <= 0:
            return
        if (
            processed_count == 1
            or processed_count == total_candidates
            or processed_count % 25 == 0
        ):
            emit_progress(
                "score_progress",
                "Scoring candidate items",
                processed_count=processed_count,
                total_count=total_candidates,
                llm_scored_count=llm_scored_count,
                fallback_scored_count=fallback_scored_count,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
            )

    for idx, item in enumerate(candidate_items, start=1):
        rules_score = rules_scores.get(item.id)
        if rules_score is None:
            emit_score_progress(idx)
            continue
        in_agent_scope = item.id in agent_scope_ids

        if not in_agent_scope:
            if profile.agent_scoring_enabled:
                policy_fallback_count += 1
            scores.append(rules_score)
            emit_score_progress(idx)
            continue

        cached_score = store.get_cached_score(
            item.hash,
            profile.openai_model,
            item_id=item.id,
            max_age_hours=24,
        )
        if cached_score is not None:
            cache_hits += 1
            llm_scored_count += 1
            scores.append(cached_score)
            emit_score_progress(idx)
            continue
        cache_misses += 1

        if agent_scorer is not None:
            if not reserve_llm_request("score"):
                fallback_reasons["budget_exhausted"] += 1
                fallback_scored_count += 1
                scores.append(rules_score)
                emit_score_progress(idx)
                continue
            score, err = _score_with_retries(
                item,
                agent_scorer,
                profile.agent_scoring_retry_attempts,
                profile.agent_scoring_text_max_chars,
            )
            if score is not None:
                llm_scored_count += 1
                scores.append(score)
                store.upsert_cached_score(item.hash, profile.openai_model, score)
                emit_score_progress(idx)
                continue
            if err is not None:
                reason = _classify_fallback_reason(str(err))
                fallback_reasons[reason] += 1
                log_event(
                    run_logger,
                    "error",
                    "score_agent",
                    "Agent scoring failed, using rules fallback",
                    item_id=item.id,
                    error=str(err),
                    fallback_reason=reason,
                )

        fallback_scored_count += 1
        scores.append(rules_score)
        emit_score_progress(idx)
    score_map = {s.item_id: s for s in scores}
    scored_items = [
        ScoredItem(item=i, score=score_map[i.id])
        for i in candidate_items
        if i.id in score_map
    ]
    log_event(
        run_logger,
        "info",
        "score",
        "Scored candidate items",
        score_count=len(scores),
        scored_item_count=len(scored_items),
    )
    emit_progress(
        "score",
        "Scored candidate items",
        score_count=len(scores),
        scored_item_count=len(scored_items),
    )

    summary_fallback_count = 0
    llm_summary_count = 0
    extractive_summary_count = 0
    llm_summary_budget_skips = 0

    quality_score: float | None = None
    quality_confidence: float | None = None
    quality_issues: list[str] = []
    quality_repair_applied = False
    quality_model = ""

    rank_overrides: dict[str, float] | None = None
    if profile.quality_learning_enabled and scored_items:
        prior_weights = store.quality_prior_weights(
            half_life_days=profile.quality_learning_half_life_days,
            max_abs_weight=profile.quality_learning_max_offset,
        )
        feedback_weights = store.feedback_feature_bias(
            max_abs_bias=max(1.0, profile.quality_learning_max_offset / 2.0)
        )
        rank_overrides = build_rank_overrides(
            scored_items,
            prior_weights=prior_weights,
            feedback_weights=feedback_weights,
            max_offset=profile.quality_learning_max_offset,
        )
        log_event(
            run_logger,
            "info",
            "quality_learning",
            "Applied quality learning priors",
            prior_feature_count=len(prior_weights),
            feedback_feature_count=len(feedback_weights),
            max_offset=profile.quality_learning_max_offset,
            half_life_days=profile.quality_learning_half_life_days,
        )
        emit_progress(
            "quality_learning",
            "Applied quality learning priors",
            prior_feature_count=len(prior_weights),
            feedback_feature_count=len(feedback_weights),
        )

    ranked_items = rank_scored_items(scored_items, rank_overrides=rank_overrides)
    ranked_non_videos = [si for si in ranked_items if si.item.type != "video"]
    sections = select_digest_sections(
        scored_items,
        rank_overrides=rank_overrides,
        must_read_max_per_source=profile.must_read_max_per_source,
    )

    if profile.quality_repair_enabled and ranked_non_videos and sections.must_read:
        candidate_pool = ranked_non_videos[: profile.quality_repair_candidate_pool_size]
        if len(candidate_pool) >= 5 and len(sections.must_read) >= 5:
            before_ids = [si.item.id for si in sections.must_read]
            quality_model = profile.quality_repair_model or profile.openai_model
            try:
                log_event(
                    run_logger,
                    "info",
                    "quality_judge_start",
                    "Starting Must-read quality judge",
                    threshold=profile.quality_repair_threshold,
                    candidate_pool_size=len(candidate_pool),
                    model=quality_model,
                )
                emit_progress(
                    "quality_judge_start",
                    "Starting Must-read quality judge",
                    threshold=profile.quality_repair_threshold,
                    candidate_pool_size=len(candidate_pool),
                    model=quality_model,
                )
                if not reserve_llm_request("quality_repair"):
                    log_event(
                        run_logger,
                        "info",
                        "quality_repair_skipped",
                        "Skipped Must-read repair due to LLM budget",
                        max_llm_requests_per_run=max_llm_requests_per_run,
                        llm_requests_used=llm_requests_used,
                    )
                    emit_progress(
                        "quality_repair_skipped",
                        "Skipped Must-read repair due to LLM budget",
                        max_llm_requests_per_run=max_llm_requests_per_run,
                        llm_requests_used=llm_requests_used,
                    )
                else:
                    quality_judge = ResponsesAPIQualityRepair(model=quality_model)
                    repair_result = quality_judge.evaluate_and_repair(
                        current_must_read=sections.must_read,
                        candidate_pool=candidate_pool,
                    )
                    quality_score = float(repair_result.quality_score)
                    quality_confidence = float(repair_result.confidence)
                    quality_issues = list(repair_result.issues)
                    log_event(
                        run_logger,
                        "info",
                        "quality_judge_result",
                        "Must-read quality judge returned result",
                        quality_score=round(quality_score, 2),
                        confidence=round(quality_confidence, 3),
                        issues=quality_issues,
                    )
                    emit_progress(
                        "quality_judge_result",
                        "Must-read quality judge returned result",
                        quality_score=round(quality_score, 2),
                        confidence=round(quality_confidence, 3),
                    )

                    after_ids = before_ids
                    if quality_score < profile.quality_repair_threshold:
                        sections = rebuild_sections_with_repair(
                            sections,
                            ranked_non_videos,
                            repair_result.repaired_must_read_ids,
                        )
                        after_ids = [si.item.id for si in sections.must_read]
                        quality_repair_applied = True
                        log_event(
                            run_logger,
                            "info",
                            "quality_repair_applied",
                            "Applied Must-read online repair",
                            quality_score=round(quality_score, 2),
                            threshold=profile.quality_repair_threshold,
                            issues=quality_issues,
                            before_ids=before_ids,
                            after_ids=after_ids,
                        )
                        emit_progress(
                            "quality_repair_applied",
                            "Applied Must-read online repair",
                            quality_score=round(quality_score, 2),
                            threshold=profile.quality_repair_threshold,
                        )
                    else:
                        log_event(
                            run_logger,
                            "info",
                            "quality_repair_skipped",
                            "Skipped Must-read repair due to quality score",
                            quality_score=round(quality_score, 2),
                            threshold=profile.quality_repair_threshold,
                            issues=quality_issues,
                        )
                        emit_progress(
                            "quality_repair_skipped",
                            "Skipped Must-read repair due to quality score",
                            quality_score=round(quality_score, 2),
                            threshold=profile.quality_repair_threshold,
                        )

                    store.insert_quality_eval(
                        run_id=run_id,
                        quality_score=quality_score,
                        confidence=quality_confidence,
                        issues=quality_issues,
                        before_ids=before_ids,
                        after_ids=after_ids,
                        repaired=quality_repair_applied,
                        model=quality_model,
                    )

                    if profile.quality_learning_enabled and after_ids != before_ids:
                        feature_map = {
                            si.item.id: item_features(si)
                            for si in ranked_non_videos[
                                : profile.quality_repair_candidate_pool_size
                            ]
                        }
                        deltas = compute_repair_feature_deltas(
                            before_ids,
                            after_ids,
                            feature_map=feature_map,
                        )
                        store.apply_quality_prior_deltas(
                            deltas,
                            max_abs_weight=profile.quality_learning_max_offset,
                        )
                        log_event(
                            run_logger,
                            "info",
                            "quality_learning_update",
                            "Updated quality priors from repair decisions",
                            delta_feature_count=len(deltas),
                        )
                        emit_progress(
                            "quality_learning_update",
                            "Updated quality priors from repair decisions",
                            delta_feature_count=len(deltas),
                        )
            except Exception as exc:
                log_event(
                    run_logger,
                    "error",
                    "quality_repair",
                    "Online quality repair failed",
                    error=str(exc),
                    fail_open=profile.quality_repair_fail_open,
                )
                emit_progress(
                    "quality_repair",
                    "Online quality repair failed",
                    error=str(exc),
                    fail_open=profile.quality_repair_fail_open,
                )
                if not profile.quality_repair_fail_open:
                    summary_errors.append(f"quality_repair: {exc}")
        else:
            log_event(
                run_logger,
                "info",
                "quality_repair_skipped",
                "Skipped Must-read repair due to insufficient candidates",
                candidate_pool_size=len(candidate_pool),
                must_read_count=len(sections.must_read),
            )
            emit_progress(
                "quality_repair_skipped",
                "Skipped Must-read repair due to insufficient candidates",
                candidate_pool_size=len(candidate_pool),
                must_read_count=len(sections.must_read),
            )

    selected_items: list[ScoredItem] = []
    selected_ids: set[str] = set()
    for scored in sections.must_read + sections.skim + sections.videos:
        if scored.item.id in selected_ids:
            continue
        selected_ids.add(scored.item.id)
        selected_items.append(scored)

    extractive_summarizer = ExtractiveSummarizer()
    llm_summarizer: FallbackSummarizer | None = None
    summary_llm_limit = min(
        len(selected_items),
        max(0, int(profile.max_llm_summaries_per_run)),
    )
    if profile.llm_enabled and summary_llm_limit > 0:
        try:
            llm_summarizer = FallbackSummarizer(
                primary=ResponsesAPISummarizer(model=profile.openai_model),
                fallback=extractive_summarizer,
            )
        except Exception as exc:
            summary_errors.append(f"llm_init: {exc}")

    log_event(
        run_logger,
        "info",
        "summarize_scope",
        "Summarizing selected digest items",
        selected_count=len(selected_items),
        max_llm_summaries_per_run=summary_llm_limit,
    )
    emit_progress(
        "summarize_scope",
        "Summarizing selected digest items",
        selected_count=len(selected_items),
        max_llm_summaries_per_run=summary_llm_limit,
    )

    for idx, scored in enumerate(selected_items, start=1):
        use_llm = llm_summarizer is not None and idx <= summary_llm_limit
        if use_llm and not reserve_llm_request("summarize"):
            llm_summary_budget_skips += 1
            use_llm = False

        if use_llm and llm_summarizer is not None:
            summary, err = llm_summarizer.summarize(scored.item)
            llm_summary_count += 1
            if err:
                summary_fallback_count += 1
                summary_errors.append(f"{scored.item.id}: {err}")
                log_event(
                    run_logger,
                    "error",
                    "summarize",
                    "Summary fallback used",
                    item_id=scored.item.id,
                    error=err,
                )
        else:
            summary = extractive_summarizer.summarize(scored.item)
            extractive_summary_count += 1

        scored.summary = summary
        if idx == 1 or idx == len(selected_items) or idx % 10 == 0:
            emit_progress(
                "summarize_progress",
                "Summarizing selected digest items",
                processed_count=idx,
                total_count=len(selected_items),
                llm_item_count=llm_summary_count,
                extractive_item_count=extractive_summary_count,
                fallback_count=summary_fallback_count,
                budget_skip_count=llm_summary_budget_skips,
            )

    emit_progress(
        "summarize",
        "Summarized selected digest items",
        item_count=len(selected_items),
        llm_item_count=llm_summary_count,
        extractive_item_count=extractive_summary_count,
        fallback_count=summary_fallback_count,
        budget_skip_count=llm_summary_budget_skips,
    )

    # Keep note naming aligned with run window timestamps (UTC) to avoid
    # local-time drift where repeated runs overwrite the previous-day note.
    date_str = now.date().isoformat()

    telegram_messages = render_telegram_messages(
        date_str,
        sections,
        render_mode=profile.output.render_mode,
    )
    if not preview_mode:
        _write_latest_telegram_artifact(run_id, telegram_messages)
    note = render_obsidian_note(
        date_str,
        sections,
        source_count=len(candidate_items),
        run_id=run_id,
        generated_at_utc=now.isoformat(),
        render_mode=profile.output.render_mode,
    )

    llm_coverage = (llm_scored_count / agent_scope_count) if agent_scope_count else 1.0
    fallback_share = (
        (fallback_scored_count / agent_scope_count) if agent_scope_count else 0.0
    )
    if profile.agent_scoring_enabled:
        log_event(
            run_logger,
            "info",
            "score_coverage",
            "LLM classification coverage",
            eligible_count=eligible_count,
            agent_scope_count=agent_scope_count,
            llm_scored_count=llm_scored_count,
            fallback_scored_count=fallback_scored_count,
            policy_fallback_count=policy_fallback_count,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            llm_coverage=round(llm_coverage, 4),
            fallback_share=round(fallback_share, 4),
            fallback_reasons=dict(fallback_reasons),
            min_llm_coverage=profile.min_llm_coverage,
            max_fallback_share=profile.max_fallback_share,
        )

    status = "success"
    if source_errors or summary_errors:
        status = "partial"
    if (
        profile.agent_scoring_enabled
        and agent_scope_count > 0
        and (
            llm_coverage < profile.min_llm_coverage
            or fallback_share > profile.max_fallback_share
        )
    ):
        summary_errors.append(
            (
                "scoring_coverage_below_threshold:"
                f" llm_coverage={llm_coverage:.3f} (min={profile.min_llm_coverage:.3f}),"
                f" fallback_share={fallback_share:.3f} (max={profile.max_fallback_share:.3f}),"
                f" agent_scope_count={agent_scope_count},"
                f" policy_fallback_count={policy_fallback_count},"
                f" reasons={json.dumps(dict(fallback_reasons), ensure_ascii=True)}"
            )
        )
        status = "partial"
    if not raw_items and source_errors:
        status = "failed"

    if (
        not preview_mode
        and profile.output.telegram_bot_token
        and profile.output.telegram_chat_id
    ):
        try:
            for idx, chunk in enumerate(telegram_messages, start=1):
                send_telegram_message(
                    profile.output.telegram_bot_token,
                    profile.output.telegram_chat_id,
                    chunk,
                )
                log_event(
                    run_logger,
                    "info",
                    "deliver_telegram",
                    "Telegram message sent",
                    chunk_index=idx,
                    chunk_count=len(telegram_messages),
                )
                emit_progress(
                    "deliver_telegram",
                    "Telegram message sent",
                    chunk_index=idx,
                    chunk_count=len(telegram_messages),
                )
        except Exception as exc:
            source_errors.append(f"telegram: {exc}")
            status = "partial"
            log_event(
                run_logger,
                "error",
                "deliver_telegram",
                "Telegram delivery failed",
                error=str(exc),
            )
            emit_progress(
                "deliver_telegram",
                "Telegram delivery failed",
                error=str(exc),
            )

    if not preview_mode and profile.output.obsidian_vault_path:
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
            log_event(
                run_logger,
                "info",
                "deliver_obsidian",
                "Obsidian note written",
                path=str(out_path),
            )
            emit_progress(
                "deliver_obsidian",
                "Obsidian note written",
                path=str(out_path),
            )
        except Exception as exc:
            source_errors.append(f"obsidian: {exc}")
            status = "partial"
            log_event(
                run_logger,
                "error",
                "deliver_obsidian",
                "Obsidian write failed",
                error=str(exc),
            )
            emit_progress(
                "deliver_obsidian",
                "Obsidian write failed",
                error=str(exc),
            )

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
        llm_coverage=round(llm_coverage, 4),
        fallback_share=round(fallback_share, 4),
        agent_scope_count=agent_scope_count,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        policy_fallback_count=policy_fallback_count,
        quality_repair_enabled=profile.quality_repair_enabled,
        quality_repair_applied=quality_repair_applied,
        quality_score=round(quality_score, 2) if quality_score is not None else None,
        quality_confidence=(
            round(quality_confidence, 3) if quality_confidence is not None else None
        ),
        quality_issues=quality_issues,
        quality_model=quality_model,
        preview_mode=preview_mode,
        source_error_count=len(source_errors),
        summary_error_count=len(summary_errors),
        final_item_count=len(selected_items),
        llm_summary_count=llm_summary_count,
        extractive_summary_count=extractive_summary_count,
        llm_summary_budget_skips=llm_summary_budget_skips,
        llm_requests_used=llm_requests_used,
        max_llm_requests_per_run=max_llm_requests_per_run,
    )
    emit_progress(
        "run_finish",
        "Digest run finished",
        status=status,
        preview_mode=preview_mode,
        source_error_count=len(source_errors),
        summary_error_count=len(summary_errors),
        final_item_count=len(selected_items),
        llm_requests_used=llm_requests_used,
        max_llm_requests_per_run=max_llm_requests_per_run,
    )

    return RunReport(
        run_id=run_id,
        status=status,
        source_errors=source_errors,
        summary_errors=summary_errors,
        telegram_messages=telegram_messages,
        obsidian_note=note,
        source_count=len(candidate_items),
        must_read_count=len(sections.must_read),
        skim_count=len(sections.skim),
        video_count=len(sections.videos),
    )


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


def _score_with_retries(
    item: Item,
    agent_scorer: ResponsesAPIScorerTagger,
    retry_attempts: int,
    max_text_chars: int,
):
    total_attempts = max(1, 1 + int(retry_attempts))
    last_exc: Exception | None = None
    for attempt in range(total_attempts):
        text_limit = max(400, int(max_text_chars / (2**attempt)))
        try:
            return agent_scorer.score_and_tag(item, max_text_chars=text_limit), None
        except (
            Exception
        ) as exc:  # pragma: no cover - behavior validated through runtime tests
            last_exc = exc
            continue
    return None, last_exc


def _classify_fallback_reason(error_text: str) -> str:
    text = (error_text or "").lower()
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "429" in text or "rate" in text:
        return "rate_limit"
    if (
        "invalid schema" in text
        or "non-json" in text
        or "missing structured json" in text
    ):
        return "invalid_schema"
    if "empty response" in text:
        return "empty_response"
    return "api_error"
