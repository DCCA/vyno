# Tasks: Web Console Density Fixes (Sources-Focused)

- [x] 1.1 Confirm UI-only scope and no backend/API changes.
- [x] 1.2 Capture current source-surface feature inventory to preserve parity.
- [x] 1.3 Confirm responsive acceptance targets (desktop/tablet/mobile).

- [x] 2.1 Implement `Sources` sub-surface hierarchy (`Overview`, `Effective Sources`, `Source Health`).
- [x] 2.2 Keep source mutation controls prominent and always visible.
- [x] 2.3 Add compact source summary metrics for quick triage.

- [x] 3.1 Refactor `Effective Sources` rendering for compact rows and truncation.
- [x] 3.2 Add full-value reveal behavior for truncated source values.
- [x] 3.3 Add lightweight filter/search and bounded initial row count with reveal option.

- [x] 4.1 Refactor `Source Health` rendering for compact triage-oriented rows.
- [x] 4.2 Add bounded initial row count with reveal option.
- [x] 4.3 Keep all existing diagnostic fields accessible.

- [x] 5.1 Apply desktop/tablet/mobile layout adjustments for dense sections.
- [x] 5.2 Verify mobile adaptive rendering for dense source data.
- [x] 5.3 Preserve navigation usability when collapsed/expanded on smaller viewports.

- [x] 6.1 Preserve loading/disabled states for source actions.
- [x] 6.2 Preserve polling-driven status behavior and non-blocking transitions.
- [x] 6.3 Preserve notice/error feedback semantics.

- [x] 7.1 Add/update frontend contract tests for new source-density behavior.
- [x] 7.2 Run frontend tests (`node --test web/tests/*.mjs`).
- [x] 7.3 Run frontend build (`npm --prefix web run build`).
- [x] 7.4 Run backend regression suite (`make test`).

- [x] 8.1 Perform manual QA for source workflows on desktop/tablet/mobile.
- [x] 8.2 Perform keyboard/focus and reduced-motion checks.
- [x] 8.3 Record QA artifacts and outcomes in design/completion notes.

- [x] 9.1 Update docs with final implementation notes and verification evidence.
- [x] 9.2 Move change to `.docs/done/` with completion summary after sign-off.
