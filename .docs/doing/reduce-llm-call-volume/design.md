# Design: reduce-llm-call-volume

## Runtime changes
- Add `max_llm_summaries_per_run` and `max_llm_requests_per_run` to `ProfileConfig`.
- Introduce a lightweight runtime budget counter that gates all LLM call sites:
  - agent scoring (cache miss path)
  - LLM summarization
  - quality-repair judge
- Move summarization from "all scored items" to "selected delivery items".

## Scope control changes
- Add `allow_seen_fallback` runtime flag (default true for compatibility).
- Set web and bot live-run defaults to incremental:
  - `use_last_completed_window=True`
  - `only_new=True`
  - `allow_seen_fallback=False`

## Telemetry changes
- Emit and log summary-scope + budget usage:
  - selected summary count
  - llm summary attempts
  - llm request budget used / configured
- Keep existing run status semantics (`success`/`partial`/`failed`).

## Testing strategy
- Extend runtime integration tests for:
  - selected-items-only summarization behavior
  - budget-exhausted fail-open behavior
  - no-seen-fallback behavior in incremental mode
- Extend config tests for new profile fields.
