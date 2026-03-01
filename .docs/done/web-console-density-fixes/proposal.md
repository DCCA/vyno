# Proposal: Web Console Density Fixes (Sources-Focused)

## Why
The redesigned console improves structure, but the `Sources` workflow remains visually dense and hard to scan. Large tables and long source strings dominate the page, reducing operator speed for routine source maintenance.

## Scope
- Redesign `Sources` surface density and information hierarchy.
- Improve readability and scanability of `Effective Sources` and `Source Health` views.
- Add responsive behavior improvements for desktop, tablet, and mobile in high-density areas.
- Preserve all existing features and backend/API behavior.

## Out of Scope
- Backend/API changes.
- Source ingestion logic changes.
- Policy/rules semantic changes.
- Removing existing source-management capabilities.

## Success Signals
- Operators can identify failing sources and apply source changes with less scrolling.
- Source tables become readable on desktop and usable on tablet/mobile.
- Existing loading/progress/error states remain intact.
- No regressions in existing source management and run workflows.
