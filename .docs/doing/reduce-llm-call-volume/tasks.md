# Tasks: reduce-llm-call-volume

- [ ] 1.0 Add profile guardrails for LLM call volume
  - [ ] 1.1 Add `max_llm_summaries_per_run` to config model + parsing
  - [ ] 1.2 Add `max_llm_requests_per_run` to config model + parsing
  - [ ] 1.3 Update config tests for new fields

- [ ] 2.0 Reduce runtime LLM call footprint
  - [ ] 2.1 Add runtime LLM budget gating helper
  - [ ] 2.2 Summarize only final selected digest items
  - [ ] 2.3 Gate quality-repair LLM call by budget
  - [ ] 2.4 Add/adjust runtime tests for summary scope and budget behavior

- [ ] 3.0 Tighten interactive run scope defaults
  - [ ] 3.1 Add `allow_seen_fallback` runtime option
  - [ ] 3.2 Use incremental options in web live-run launcher
  - [ ] 3.3 Use incremental options in telegram bot live-run launcher
  - [ ] 3.4 Add tests for no-seen-fallback behavior

- [ ] 4.0 Verify and close
  - [ ] 4.1 Run full test suite
  - [ ] 4.2 Run web build
  - [ ] 4.3 Update docs/tasks to reflect final behavior and any deferrals
