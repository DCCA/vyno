# Project Review and Backlog (2026-02-22)

## Current State Review
- Core digest pipeline is working end-to-end: ingestion, normalization, scoring/tagging, selection, Telegram delivery, and Obsidian archive.
- Source coverage includes RSS, YouTube, X inbox links, and GitHub API selectors.
- Agent scoring/tagging via OpenAI Responses API is implemented with per-item rules fallback.
- Structured JSON logs with `run_id` and stage events are in place (`logs/digest.log`).
- Obsidian naming supports `timestamped` (default) and `daily` compatibility mode.
- Test suite is healthy (`make test` passing, 26 tests).

## Key Risks / Gaps
- Runtime can be slow/costly with agent scoring on many items per run.
- X ingestion is manual-link based only (no native API metadata).
- GitHub ingestion currently fetches broad sets; needs tighter quality filters.
- No explicit score caching yet; repeated runs can rescore identical items.
- No SLO dashboard or alerting for delivery failures.

## Backlog (Tomorrow)

### P0 (Do First)
- [ ] Add score caching by item hash + model for 24h.
  - Done when repeated run reuses cached score/tag for unchanged items.
- [ ] Add agent scoring cap (`max_agent_items_per_run`, default 40).
  - Done when runs above cap still complete with rules fallback for overflow.
- [ ] Add per-source quality filters for GitHub (stars/updated windows) and X inbox sanity rules.
  - Done when low-signal GitHub/X noise decreases in top sections.

### P1 (High Value)
- [ ] Add digest quality guardrails in runtime:
  - enforce non-empty Must-read when source_count > 0,
  - log section sizes and fallback reasons.
- [ ] Add DB indexes (`scores.run_id`, `items.hash`, `seen.key`) and verify runtime impact.
- [ ] Add `make smoke` command (live run + DB/log sanity checks summary).

### P2 (Next Iteration)
- [ ] Add optional daily index note in Obsidian folder linking timestamped runs.
- [ ] Add “Code & Repos” subsection in rendering when GitHub items exist.
- [ ] Add lightweight report command (`make report`) for yesterday’s run KPIs.

## Suggested Execution Order
1. Score caching + agent cap (performance/cost control).
2. GitHub/X quality filters (signal improvement).
3. Runtime guardrails + smoke/report commands (operability).

## Validation Checklist for Tomorrow
- [ ] `make test` passes.
- [ ] `make live` succeeds.
- [ ] Log contains expected run stages and no unhandled errors.
- [ ] Obsidian note contains non-empty Must-read for active-source runs.
