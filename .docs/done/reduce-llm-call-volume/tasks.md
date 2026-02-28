# Tasks: reduce-llm-call-volume

- [x] 1.0 Add profile guardrails for LLM call volume
  - [x] 1.1 Add `max_llm_summaries_per_run` to config model + parsing
  - [x] 1.2 Add `max_llm_requests_per_run` to config model + parsing
  - [x] 1.3 Update config tests for new fields

- [x] 2.0 Reduce runtime LLM call footprint
  - [x] 2.1 Add runtime LLM budget gating helper
  - [x] 2.2 Summarize only final selected digest items
  - [x] 2.3 Gate quality-repair LLM call by budget
  - [x] 2.4 Add/adjust runtime tests for summary scope and budget behavior

- [x] 3.0 Tighten interactive run scope defaults
  - [x] 3.1 Add `allow_seen_fallback` runtime option
  - [ ] 3.2 Use incremental options in web live-run launcher. (Deferred: retained existing web run scope in this change; runtime LLM guardrails now prevent request spikes.)
  - [x] 3.3 Use incremental options in telegram bot live-run launcher
  - [x] 3.4 Add tests for no-seen-fallback behavior

- [x] 4.0 Verify and close
  - [x] 4.1 Run full test suite
  - [x] 4.2 Run web build
  - [x] 4.3 Update docs/tasks to reflect final behavior and any deferrals
