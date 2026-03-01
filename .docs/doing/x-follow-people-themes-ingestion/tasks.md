# Tasks: X Follow People + Theme Ingestion

## 1. Config and Registry Foundation
- [ ] 1.1 Extend `SourceConfig` with `x_authors` and `x_themes`.
- [ ] 1.2 Extend source registry field mapping and canonicalization for `x_author` and `x_theme`.
- [ ] 1.3 Ensure source listing and overlays include new X selector types.

## 2. Provider and Connector Layer
- [ ] 2.1 Add X provider router abstraction (`inbox_only`, `x_api`).
- [ ] 2.2 Implement selector connector for author/theme fetch with bounded limits.
- [ ] 2.3 Preserve existing inbox connector and merge outputs safely.

## 3. Cursoring and Storage
- [ ] 3.1 Add `x_selector_cursors` table migration in SQLite store.
- [ ] 3.2 Add get/set cursor methods and wire into selector fetch loop.
- [ ] 3.3 Add tests for cursor persistence and idempotent table initialization.

## 4. Runtime and Error Surfaces
- [ ] 4.1 Integrate selector ingestion in runtime fetch stage.
- [ ] 4.2 Emit structured per-selector source errors with `x_author:` / `x_theme:` prefixes.
- [ ] 4.3 Extend web source-health parser and hint mapping for new X error kinds.

## 5. Operator Controls (Web + Bot)
- [ ] 5.1 Ensure web source type APIs expose `x_author` and `x_theme`.
- [ ] 5.2 Validate web source add/remove/list UX for new selector types.
- [ ] 5.3 Validate Telegram `/source` command and wizard flows for new selector types.

## 6. Verification
- [ ] 6.1 Add/extend unit tests for source canonicalization and connector normalization.
- [ ] 6.2 Add/extend integration tests for mixed-mode runs and source health outputs.
- [ ] 6.3 Run frontend tests for source management parity.
- [ ] 6.4 Document env/config migration notes in README and `.docs/done/...` on completion.
