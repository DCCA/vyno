# Design: Web Console UI Redesign (No Regression)

## Design Intent
Adopt a status-first operations console with progressive disclosure:
- Show critical health and run actions first.
- Move dense diagnostics and advanced controls behind focused pages/sections.
- Keep all existing capabilities while reducing visual clutter.

## IA and Surface Model
Proposed primary surfaces:
- Dashboard: run health, key alerts, quick actions.
- Run Center: run initiation, mode override, live progress, strictness/funnel, recommendations.
- Sources & Policy: source CRUD, source health diagnostics, run policy controls, seen maintenance.
- Onboarding: preflight, source packs, preview, activate.
- Timeline & Notes: events, summary, notes, export.
- History & Rollback: snapshots and restore actions.

## Implementation Strategy
### 1) Structural Refactor First
- Decompose `web/src/App.tsx` into focused feature modules and shared shell/layout components.
- Introduce page-level composition with shared top bar, alert system, and action region.
- Keep existing API calls and state semantics intact during decomposition.

### 2) Styling System Refresh
- Consolidate spacing, typography, card variants, and table density tokens.
- Reduce simultaneous visual emphasis by introducing stronger content hierarchy.
- Preserve current color intent while improving contrast and scanability.

### 3) Motion System
- Add lightweight CSS/Tailwind transitions for:
  - page/section enter
  - status badge and loading transitions
  - progress updates
  - panel expand/collapse
- Respect `prefers-reduced-motion` by disabling or minimizing non-essential effects.

### 4) State Integrity Constraints
- Preserve all existing async flags and notices (`loading`, `saving`, `runNowLoading`, `previewLoading`, `activateLoading`).
- Preserve polling cadence and logic for run status/progress/timeline.
- Preserve endpoint payload shapes and action guards.

## Verification Approach
- Contract check that all existing actions remain reachable from redesigned navigation.
- Regression checks:
  - `make test`
  - `npm --prefix web run build`
- Manual UX checks:
  - run-now start/active/complete/error flows
  - onboarding preflight/preview/activate
  - source add/remove and health diagnostics
  - run policy save and seen reset preview/apply
  - timeline filters/export/notes
  - snapshot rollback
- Accessibility checks:
  - keyboard navigation and visible focus
  - reduced motion behavior
  - mobile viewport layout sanity

## Implementation Notes (2026-03-01)
- Introduced a surface-based navigation shell in `web/src/App.tsx`:
  - `dashboard`, `run`, `onboarding`, `sources`, `profile`, `review`, `timeline`, `history`.
- Kept existing API action handlers/state wiring in-place (no contract changes).
- Preserved existing loading and progress state flags and disabled-state behavior.
- Added lightweight motion utility `.animate-surface-enter` with reduced-motion fallback in `web/src/index.css`.

## Manual QA Notes (2026-03-01)
- Browser automation QA executed against local UI using `agent-browser`.
- Validated navigation and controls across:
  - Desktop
  - Tablet (`900x1200`)
  - Mobile (`390x844`)
- Validated keyboard focus traversal (`Tab`) and reduced-motion media preference.
- Validated loading-state behavior with onboarding preview (`Run preview` showing `Running...`, related controls disabled).
- QA screenshots saved under `/tmp/vyno-ui-qa/`:
  - `desktop-dashboard.png`
  - `desktop-run-center.png`
  - `desktop-sources.png`
  - `desktop-profile.png`
  - `tablet-onboarding-navclosed.png`
  - `tablet-onboarding-navopen.png`
  - `mobile-onboarding-navclosed.png`
  - `mobile-onboarding-navopen.png`

## Risks and Mitigations
- Risk: UI-only refactor accidentally drops behavior wiring.
  - Mitigation: implement in phased slices and validate feature parity per phase.
- Risk: motion harms responsiveness.
  - Mitigation: short durations, transform/opacity-only transitions, reduced-motion fallback.
- Risk: large `App.tsx` refactor causes merge complexity.
  - Mitigation: isolate shell/page extraction first, then visual changes.
