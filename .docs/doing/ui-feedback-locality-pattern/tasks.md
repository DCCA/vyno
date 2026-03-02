# Tasks: UI Feedback Locality Pattern

## 1. Foundation
- [ ] 1.1 Add a shared feedback type/helper with severity + timestamp.
- [ ] 1.2 Add `SectionFeedback` rendering primitive (inline alert + dismiss + live-region semantics).
- [ ] 1.3 Keep global notice only for bootstrap/system failures.

## 2. Section Migration (web/src/App.tsx)
- [ ] 2.1 Migrate Sources actions (`add`, `remove`, `edit prefill`, row delete).
- [ ] 2.2 Migrate Run Center actions (`run now`, onboarding preview/activate, packs, preflight).
- [ ] 2.3 Migrate Profile/Review actions (`validate`, `diff`, `save`, run policy save).
- [ ] 2.4 Migrate Timeline/History actions (note save, export, rollback, seen reset).

## 3. Behavior Consistency
- [ ] 3.1 Add success auto-dismiss with hover/focus pause.
- [ ] 3.2 Keep errors sticky; add explicit dismiss control.
- [ ] 3.3 Ensure retry action clears prior success in same section.

## 4. QA and Verification
- [ ] 4.1 Update/add frontend tests asserting section-local feedback placement.
- [ ] 4.2 Validate desktop/tablet/mobile feedback visibility without scrolling.
- [ ] 4.3 Validate keyboard navigation and `aria-live` behavior.
- [ ] 4.4 Run `npm --prefix web run test` and `npm --prefix web run build`.
