# Proposal: Web Console Signal Deck Redesign

## Why
The current web console remains information-dense and visually noisy in key surfaces (dashboard, effective sources, source health). Operators can access features, but scan speed and hierarchy are weak under real run pressure.

This redesign aims to improve legibility, flow, and trust while preserving all existing behavior.

## Problem Statement
- Critical actions and statuses compete visually instead of guiding operator attention.
- Dense tables dominate above-the-fold space and reduce discoverability of run-state cues.
- The current system works functionally but does not communicate confidence, calm, or control.

## Goals
- Preserve 100% of existing capability and API behavior.
- Improve visual hierarchy and scanning speed for run operations.
- Reduce perceived clutter without hiding operational detail.
- Add intentional motion and loading choreography that clarifies state transitions.
- Deliver coherent responsive behavior for desktop, tablet, and mobile.

## Non-Goals
- No backend API contract changes.
- No feature removals.
- No rewrite of domain logic or run pipeline behavior.

## Design Direction (frontend-design skill)
**Concept:** `Signal Deck`
- Tone: editorial-operations hybrid; high-contrast control room in light mode.
- Differentiator: one unmistakable visual pattern of "status ribbons + layered cards" that makes run state and health visible in one glance.
- Typography: distinctive display + readable body pairing (non-generic).
- Motion: purposeful stage transitions, skeleton/loading choreography, and section reveal timing.
- Spatial system: breathing room at top-level surfaces, controlled density inside data views.

## Success Criteria
- Operators can identify active run status, errors, and next action in under 5 seconds on dashboard.
- Source health issues are visible without scrolling past unrelated content.
- Time-to-interaction and perceived responsiveness are improved with preserved/clear loading states.
- Layout quality is maintained at mobile, tablet, and desktop breakpoints.
- Accessibility and interaction quality meet WCAG-oriented contrast, keyboard, and touch-target expectations.
- UI state is shareable for key surfaces (deep-linkable surface/tab context) where practical.
