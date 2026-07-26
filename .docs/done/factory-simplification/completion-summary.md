# Completion Summary: factory-simplification

**Shipped:** 2026-07-26, PRs #30, #31, #32 (this PR).
**Proposal:** approved 2026-07-26 (Tier 0 + Tier 1, keep X untouched, Tier 2 Option A, paste-a-link, engineer loop). Full proposal and tasks recoverable from git history of `.docs/doing/factory-simplification/`.

## What shipped

**PR #30 - Tier 0 hygiene.** Removed the tracked Remotion `video/` project (~3,850 lines), `requirements.txt` (Docker now installs `.[runtime,llm]` from pyproject), and five dead functions.

**PR #31 - Option A + Tier 1 + paste-a-link.** Retired the web console: React frontend (`web/`) and FastAPI control plane (`src/digest/web/`) deleted; Telegram bot + CLI are the operator surface; single-stage Dockerfile; frontend CI job removed. Tier 1: deepagents repair path (+dependency), `render_mode`, `obsidian_naming`, `youtube_queries`, orphaned `source_buckets.py`. New: `/source add <url-or-handle>` auto-detects the connector (github repo/org/topic, x author, youtube channel incl. page-resolved handles, rss autodiscovery), preflights, one wizard confirm; structurally-valid-but-unsupported links become `feedback` rows with `label='ingest_suggestion'`. The `digest schedule` loop became profile-driven (honors `profile.schedule` as edited by `/schedule`, exactly-once slots via `.runtime/schedule-state.json`, same-day catch-up) - fixing a review-found blocker where the dockerized scheduler ignored bot edits after the console removal. Net: -19,007/+1,051 lines across 163 files.

**PR #32 - Engineer loop.** Standing brief in `AGENTS.md` (read-only SQL inputs, one-PR-per-cycle, evidence requirements, hard fences, no-PR-is-success). First supervised cycle ran against the live DB during this PR (see below).

## Review process

Each PR: multi-agent adversarial review (PR #31: 27 agents, 4 dimensions, 21 confirmed findings - all fixed) plus an independent Codex review (all 4 Codex findings overlapped the workflow's). TDD on all new behavior. Full suite + docker build green per PR.

## First supervised engineer cycle (2026-07-26)

Signals from `digest-live.db`:
- Every recent run is `partial` with 17-20 summary errors: OpenAI 429 quota exhaustion. Account state, not code - surfaced to the operator, no PR (correct no-action outcome).
- Historical `blog.langchain.com/rss/` and GitHub 422 source errors: already fixed by PRs #27/#28; absent from the last three runs. No action.
- **Actionable:** `run_quality_eval.quality_score` mixes scales (8.0/9.0 vs 88.0) against the 0-100 `quality_repair_threshold: 80`, making the repair gate meaningless for 0-10-scale responses. Queued as the engineer's first improvement PR.

## Known consequences / follow-ups

- Item-level feedback lost its only input surface (web Timeline). Source-level `/feedback mute|trust` remains. Candidate engineer task: reaction buttons on delivered digest items.
- OpenAI quota exhausted on the account: digests degrade to rules scoring + extractive summaries until topped up.
- Two pre-existing `make doctor` FAILs from root-owned bind-mount files: `sudo chown $USER:$USER data/profile.local.yaml .runtime/onboarding-state.json`.
- Engineer cadence: manual supervised cycles; schedule via cron only after 3 clean cycles.
