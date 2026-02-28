# Completion Summary: reduce-llm-call-volume

## What changed
- Added profile guardrails for LLM volume in `src/digest/config.py`:
  - `max_llm_summaries_per_run`
  - `max_llm_requests_per_run`
- Reduced runtime LLM usage in `src/digest/runtime.py`:
  - summarize only selected delivery items
  - enforce per-run LLM request budget across scoring, summarization, and quality repair
  - added `allow_seen_fallback` runtime switch to control reprocessing behavior when `only_new` has no unseen items
- Tightened bot-triggered run scope in `src/digest/ops/telegram_commands.py` to incremental defaults (`use_last_completed_window=True`, `only_new=True`, `allow_seen_fallback=False`).
- Updated default profile guardrails in `config/profile.yaml` (`max_agent_items_per_run: 20`, `max_llm_summaries_per_run: 20`, `max_llm_requests_per_run: 45`).

## Verification
- `make test` passed (`104` tests).
- `make web-ui-build` passed.

## Deferred
- Web-triggered run scope defaults were intentionally left unchanged in this change set; runtime-level LLM guardrails now cap call volume even on broad runs.

## Risk and follow-ups
- If provider rate limits remain tight for first-run backfills, lower `max_agent_items_per_run` and/or `max_llm_requests_per_run` further in `config/profile.yaml`.
- Optional follow-up: switch web-triggered runs to incremental defaults after operator validation.
