# Tasks: Web Console Signal Deck Redesign

## 1. Discovery and Baseline
- [ ] 1.1 Capture current UI screenshots for key surfaces (dashboard, sources, profile, timeline).
- [ ] 1.2 Record current loading and animation behavior by action.
- [ ] 1.3 Identify high-clutter zones and define target layout outcomes.

## 2. Visual System Foundation
- [ ] 2.1 Define design tokens (color, type, spacing, elevation, motion).
- [ ] 2.2 Implement shared surface/card primitives and status ribbon styling.
- [ ] 2.3 Add background treatment and responsive container rules.
- [ ] 2.4 Validate token-level contrast and non-color status affordances.

## 3. Surface Refactor (Parity-Safe)
- [ ] 3.1 Redesign dashboard hierarchy and activity panel composition.
- [ ] 3.2 Redesign sources views (overview/effective/health) for triage flow.
- [ ] 3.3 Redesign profile/review presentation for diff legibility.
- [ ] 3.4 Redesign timeline/history visual scan lanes.

## 4. Motion and Loading
- [ ] 4.1 Implement deterministic enter/reveal motion for top-level sections.
- [ ] 4.2 Preserve and improve action-specific loading indicators.
- [ ] 4.3 Add reduced-motion fallback behavior.
- [ ] 4.4 Align skeleton/loading geometry to final layout to minimize visual shifts.

## 5. Responsive Hardening
- [ ] 5.1 Validate desktop/tablet/mobile breakpoints.
- [ ] 5.2 Eliminate horizontal overflow and touch-target issues.
- [ ] 5.3 Tune spacing and typography scale per breakpoint.
- [ ] 5.4 Validate minimum touch ergonomics for mobile primary actions.

## 6. Semantic and State Hardening
- [ ] 6.1 Preserve semantic landmarks and heading hierarchy across major surfaces.
- [ ] 6.2 Ensure form labels, helper text, and error messaging remain explicit.
- [ ] 6.3 Persist primary surface/tab context in URL query state where practical.

## 7. Verification and Handoff
- [ ] 7.1 Execute frontend tests and document results.
- [ ] 7.2 Run manual smoke tests for all existing features.
- [ ] 7.3 Execute keyboard-only and contrast audit checks.
- [ ] 7.4 Produce before/after screenshots and QA notes.
- [ ] 7.5 Update `.docs/done/...` artifacts after implementation completes.
