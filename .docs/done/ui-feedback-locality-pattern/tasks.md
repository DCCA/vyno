# Tasks: UI Feedback Locality Pattern

## 1. Foundation
- [x] 1.1 Add a shared feedback type/helper with severity + timestamp.
- [x] 1.2 Add `SectionFeedback`-equivalent inline rendering primitive (dismiss + live-region semantics).
- [x] 1.3 Keep global notice only for bootstrap/system failures.

## 2. Section Migration (web/src/App.tsx)
- [x] 2.1 Migrate Sources actions (`add`, `remove`, `edit prefill`, row delete).
- [x] 2.2 Migrate Run Center actions (`run now`, onboarding preview/activate, packs, preflight).
- [x] 2.3 Migrate Profile/Review actions (`validate`, `diff`, `save`, run policy save).
- [x] 2.4 Migrate Timeline/History actions (note save, export, rollback, seen reset).

## 3. Behavior Consistency
- [x] 3.1 Add success auto-dismiss.
- [x] 3.2 Keep errors sticky; add explicit dismiss control.
- [x] 3.3 Ensure section-scoped replacement of stale messages.

## 4. QA and Verification
- [x] 4.1 Update/add frontend tests asserting section-local feedback placement.
- [ ] 4.2 Manual viewport walkthrough at desktop/tablet/mobile (deferred to UI QA pass).
- [x] 4.3 Validate accessibility semantics (`aria-live`) in code and tests.
- [x] 4.4 Run `npm --prefix web run test` and `npm --prefix web run build`.
