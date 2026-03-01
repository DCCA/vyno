# Proposal: UI UX Console Redesign

## Why
The current web console is functionally complete, but it still feels tab-heavy and requires too much operator interpretation during setup. The next milestone is to make first-run success obvious and to make day-2 operations faster.

## Scope
- Redesign the web console information architecture around two modes:
  - Setup Journey (task-first onboarding flow)
  - Manage Workspace (advanced controls)
- Apply an intentional visual system (typography, color, spacing, motion, surface treatment) while preserving existing API behavior and operational semantics.
- Keep all existing actions working end-to-end: preflight, source-pack apply, preview, activate, source add/remove, profile validate/diff/save, rollback, and run-now.
- Validate by automated tests, web build, and real browser E2E flow checks.

## Non-goals
- No backend API contract changes.
- No auth/multi-user feature work.
- No changes to digest ranking/runtime policy in this change.
