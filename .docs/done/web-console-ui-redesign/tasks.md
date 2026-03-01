# Tasks: Web Console UI Redesign (No Regression)

- [x] 1.1 Freeze redesign scope as presentation-only (no API/runtime behavior changes).
- [x] 1.2 Record current feature inventory from existing UI sections and actions.
- [x] 1.3 Define page-level IA map (Dashboard, Run Center, Sources & Policy, Onboarding, Timeline, History).

- [x] 2.1 Extract app shell and navigation structure from `App.tsx`.
- [x] 2.2 Split monolithic UI into focused page/section components with shared state wiring.
- [x] 2.3 Preserve existing async state flags and notice behavior through refactor.

- [x] 3.1 Implement redesigned Dashboard with status-first hierarchy.
- [x] 3.2 Implement redesigned Run Center with mode controls, progress, and strictness/funnel visibility.
- [x] 3.3 Implement redesigned Sources & Policy page with source CRUD, health, run policy, and seen maintenance.
- [x] 3.4 Migrate Onboarding, Timeline, and History surfaces into focused layouts without capability loss.

- [x] 4.1 Introduce consistent visual system updates (spacing, type hierarchy, card/table density, emphasis levels).
- [x] 4.2 Add purposeful motion transitions for page/section entry and state changes.
- [x] 4.3 Add `prefers-reduced-motion` support and verify equivalent usability.

- [x] 5.1 Verify all legacy capabilities remain reachable and functional in redesigned navigation.
- [x] 5.2 Run backend regression suite (`make test`).
- [x] 5.3 Run frontend build verification (`npm --prefix web run build`).
- [x] 5.4 Perform manual flow validation for run-now, onboarding, sources, policy, timeline, and rollback.
- [x] 5.5 Perform responsive and keyboard/focus checks.

- [x] 6.1 Update docs/design notes to reflect final implemented structure and decisions.
- [x] 6.2 Move change to `.docs/done/` with completion summary after sign-off.
