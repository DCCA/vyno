# Proposal: Web Console UI Redesign (No Regression)

## Why
The current web console is visually dense and cognitively expensive. Primary actions and critical status are mixed with advanced controls, which slows routine operation and onboarding.

## Scope
- Redesign visual presentation and information hierarchy of the web console.
- Preserve all existing backend/API behavior and feature coverage.
- Preserve existing loading/progress/error feedback semantics.
- Add intentional motion/animation for state transitions and screen affordances.
- Keep responsive behavior for desktop and mobile widths.

## Out of Scope
- Changing API contracts or runtime pipeline semantics.
- Removing existing capabilities (run modes, onboarding, timeline, rollback, seen reset, source health, profile editing).
- Rewriting backend logic.

## Success Signals
- Operators can find primary actions (`Run now`, run status, source health) without scanning long stacked panels.
- Existing user workflows continue to work with no behavior regressions.
- Loading/progress feedback remains visible and understandable across all key actions.
- UI motion improves clarity without reducing perceived responsiveness.
