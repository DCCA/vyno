# Tasks: Scoring Cache and Source Quality Filters

- [x] 1.1 Create Firehose artifacts for this change (`proposal.md`, `spec.md`, `design.md`, `tasks.md`).

- [x] 2.1 Add SQLite score cache schema and store helpers.
- [x] 2.2 Integrate score cache lookup/write in runtime agent scoring flow.
- [x] 2.3 Add `max_agent_items_per_run` config and runtime cap behavior.
- [x] 2.4 Adjust scoring coverage policy to exclude cap-overflow fallback.

- [x] 3.1 Add GitHub quality filters for stars and recency windows.
- [x] 3.2 Wire profile configuration for GitHub recency filters.
- [x] 3.3 Add X inbox normalization/dedupe/noise filtering.

- [x] 4.1 Add/extend tests for cache reuse and cap policy behavior.
- [x] 4.2 Add/extend tests for GitHub and X filtering behavior.

- [x] 5.1 Update README/profile docs for new configuration fields.
- [x] 5.2 Run test suite and confirm no regressions.
