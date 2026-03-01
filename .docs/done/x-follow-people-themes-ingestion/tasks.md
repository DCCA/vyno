# Tasks: X Follow People + Theme Ingestion

## 1. Config and Registry Foundation
- [x] 1.1 Extend `SourceConfig` with `x_authors` and `x_themes`.
- [x] 1.2 Extend source registry field mapping and canonicalization for `x_author` and `x_theme`.
- [x] 1.3 Ensure source listing and overlays include new X selector types.

## 2. Provider and Connector Layer
- [x] 2.1 Add X provider router abstraction (`inbox_only`, `x_api`).
- [x] 2.2 Implement selector connector for author/theme fetch with bounded limits.
- [x] 2.3 Preserve existing inbox connector and merge outputs safely.
- [x] 2.4 Implement endpoint mapping using official X API paths and pagination fields.

## 3. Cursoring and Storage
- [x] 3.1 Add `x_selector_cursors` table migration in SQLite store.
- [x] 3.2 Add get/set cursor methods and wire into selector fetch loop.
- [x] 3.3 Add tests for cursor persistence and idempotent table initialization.

## 4. Runtime and Error Surfaces
- [x] 4.1 Integrate selector ingestion in runtime fetch stage.
- [x] 4.2 Emit structured per-selector source errors with `x_author:` / `x_theme:` prefixes.
- [x] 4.3 Extend web source-health parser and hint mapping for new X error kinds.

## 5. Operator Controls (Web + Bot)
- [x] 5.1 Ensure web source type APIs expose `x_author` and `x_theme`.
- [x] 5.2 Validate web source add/remove/list UX for new selector types.
- [x] 5.3 Validate Telegram `/source` command and wizard flows for new selector types.

## 6. Verification
- [x] 6.1 Add/extend unit tests for source canonicalization and connector normalization.
- [x] 6.2 Add/extend integration tests for mixed-mode runs and source health outputs.
- [x] 6.3 Run frontend tests for source management parity.
- [x] 6.4 Validate behavior against official X API docs constraints (time window, query/paging, limits).
- [x] 6.5 Document env/config migration notes in README and `.docs/done/...` on completion.
