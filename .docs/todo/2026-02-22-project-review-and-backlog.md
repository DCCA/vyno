# Project Review and Backlog (2026-02-22)

## Current State Review
- Core digest pipeline is working end-to-end: ingestion, normalization, scoring/tagging, selection, Telegram delivery, and Obsidian archive.
- Source coverage includes RSS, YouTube, X inbox links, and GitHub API selectors.
- Agent scoring/tagging via OpenAI Responses API is implemented with per-item rules fallback.
- Structured JSON logs with `run_id` and stage events are in place (`logs/digest.log`).
- Obsidian naming supports `timestamped` (default) and `daily` compatibility mode.
- Test suite is healthy (`make test` passing, 94 tests).

## Key Risks / Gaps
- Runtime can still be slow/costly on source-heavy runs despite score cache + cap guardrails.
- X ingestion is manual-link based only (no native API metadata).
- No SLO dashboard or alerting for delivery failures.
- Docker runtime validation is not fully closed in docs (startup/restart/persistence checks pending on a Docker-enabled host).

## Backlog (Tomorrow)

### P0 (Do First)
- [x] Add score caching by item hash + model for 24h. (Done in `.docs/done/scoring-cache-and-source-quality/`)
  - Done when repeated run reuses cached score/tag for unchanged items.
- [x] Add agent scoring cap (`max_agent_items_per_run`, default 40). (Done in `.docs/done/scoring-cache-and-source-quality/`)
  - Done when runs above cap still complete with rules fallback for overflow.
- [x] Add per-source quality filters for GitHub (stars/updated windows) and X inbox sanity rules. (Done in `.docs/done/scoring-cache-and-source-quality/`)
  - Done when low-signal GitHub/X noise decreases in top sections.

### P1 (High Value)
- [ ] Add digest quality guardrails in runtime:
  - enforce non-empty Must-read when source_count > 0,
  - emit explicit section-size telemetry per run.
- [ ] Add DB indexes (`scores.run_id`, `items.hash`, `seen.key`) and verify runtime impact.
- [ ] Add `make smoke` command (live run + DB/log sanity checks summary).
- [ ] Close Docker runtime verification tasks (container startup, restart, and persistence) and move dockerization change to `.docs/done/`.

### P2 (Next Iteration)
- [ ] Add optional daily index note in Obsidian folder linking timestamped runs.
- [ ] Add “Code & Repos” subsection in rendering when GitHub items exist.
- [ ] Add lightweight report command (`make report`) for yesterday’s run KPIs.

## Suggested Execution Order
1. Runtime guardrails + smoke command (operability).
2. Docker runtime verification closeout on Docker-enabled host.
3. Report/SLO visibility improvements.

## Validation Checklist for Tomorrow
- [ ] `make test` passes.
- [ ] `make live` succeeds.
- [ ] Log contains expected run stages and no unhandled errors.
- [ ] Obsidian note contains non-empty Must-read for active-source runs.
