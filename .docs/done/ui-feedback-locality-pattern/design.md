# Design: UI Feedback Locality Pattern

## Current State
- `notice` is a single app-level state rendered near the top of the app shell.
- Most action handlers write into this shared state.

## Target Pattern
1. Keep a tiny global feedback channel for app-wide failures only.
2. Introduce section-scoped feedback channels:
   - Run Center feedback
   - Sources feedback
   - Profile feedback
   - Review feedback
   - Timeline feedback
   - History feedback
3. Render feedback inline in each section, directly above the action row or result table.
4. Use a shared helper for consistent shape (`kind`, `text`, optional `code`, `at`).

## Placement Rules
- Form-submit actions: message directly below the submit row.
- Table-row actions: message above the table and include target row identity.
- Destructive actions: keep inline confirmation + inline result.
- Polling/background refresh errors: section-level non-blocking hint near refresh control.

## Interaction Rules
- Success: auto-dismiss after 4-6s.
- Error: persistent until user dismisses or retry succeeds.
- New action in same section replaces stale message in that section only.

## Migration Plan
- Phase 1: Introduce section-scoped state and rendering wrappers.
- Phase 2: Move action handlers section by section from global `notice` to local channels.
- Phase 3: Restrict global banner to bootstrap/system-level failures.

## Surface Coverage Matrix
- Dashboard/Run header: keep only global/system feedback; local run actions show inline feedback near run controls.
- Sources: add/remove/edit/delete feedback rendered inside Sources card, directly above filter/table region.
- Onboarding: preflight/source-pack/preview/activate feedback rendered in onboarding cards next to triggered controls.
- Profile: profile field save + run policy save feedback rendered near profile action buttons.
- Review: validate/diff/save feedback rendered in review panel above JSON/editor area.
- Timeline: refresh/export/note-save feedback rendered near timeline toolbar and note composer.
- History: rollback feedback rendered in history panel near rollback controls.
