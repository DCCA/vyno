# Design: Web Console Density Fixes (Sources-Focused)

## Intent
Improve operational speed in the `Sources` area by reducing visual clutter while preserving all existing capabilities and behavior.

## UX Strategy
- Keep source mutation controls at top and always visible.
- Separate dense diagnostics into focused sub-surfaces:
  - `Overview`
  - `Effective Sources`
  - `Source Health`
- Use compact summary metrics above detailed data.

## Information Density Strategy
### Effective Sources
- Keep existing columns (`Type`, `Count`, `Values`) but reduce row growth:
  - constrain value column width
  - truncate long values
  - add full-value reveal on demand (title/expand/popover)
- Add a compact filter/search field to quickly locate source entries.
- Add a bounded initial row count with explicit “Show more”.

### Source Health
- Prioritize triage columns at render time:
  - source
  - failure count
  - latest error
  - suggested fix
- Use compact row styling and bounded initial row count.
- Keep full diagnostics accessible without removing data.

## Layout Strategy by Breakpoint
- Desktop:
  - retain sidebar + wide content
  - optimize table widths and sticky headers
- Tablet:
  - compact sidebar visual weight
  - maintain visibility of core source actions above fold
- Mobile:
  - default collapsed navigation
  - replace high-density table rows with adaptive stacked rows/cards when needed

## State and Behavior Constraints
- Preserve existing handlers and endpoint usage for source operations.
- Preserve loading/disabled states for source actions.
- Preserve notice/error feedback behavior.
- Preserve periodic polling and live status updates.

## Verification Plan
- Automated:
  - `node --test web/tests/*.mjs`
  - `npm --prefix web run build`
- Manual:
  - Source add/remove flows and loading states
  - Effective sources readability on long values
  - Source health triage flow
  - Desktop/tablet/mobile responsive checks
  - Keyboard focus traversal
  - Reduced-motion preference behavior

## Implementation Notes (2026-03-01)
- Implemented `Sources` density refactor in `web/src/App.tsx`:
  - Added `Sources Workspace` with sub-surfaces:
    - `Overview`
    - `Effective Sources`
    - `Source Health`
  - Added summary metrics (`types`, `total sources`, `failing sources`).
  - Added filter/search controls for effective sources and source health rows.
  - Added bounded initial row rendering with explicit `Show more` controls.
  - Added compact row rendering with truncation plus `View full values` detail reveal.
  - Added mobile-friendly stacked row cards for dense table data.
- Preserved existing source mutation flows and async loading/disabled states.
- Preserved existing API contract usage and polling behavior.

## Verification Notes (2026-03-01)
- Automated checks:
  - `node --test web/tests/*.mjs` passed (`4` tests).
  - `npm --prefix web run build` passed.
  - `make test` passed (`141` tests).
- Manual browser QA completed with `agent-browser` on `Sources` surface:
  - Desktop
  - Tablet (`900x1200`)
  - Mobile (`390x844`)
- Accessibility checks completed:
  - Keyboard focus traversal (`Tab`) confirmed
  - Reduced-motion media preference confirmed (`prefers-reduced-motion: reduce` => `true`)
- QA screenshots saved in `/tmp/vyno-ui-density-qa/`:
  - `desktop-sources-overview.png`
  - `desktop-sources-effective.png`
  - `desktop-sources-health.png`
  - `tablet-sources-health.png`
  - `tablet-sources-health-navopen.png`
  - `mobile-sources-health-navopen.png`
  - `mobile-sources-health-navclosed.png`

## Risks and Mitigations
- Risk: density reduction hides useful detail.
  - Mitigation: truncation with explicit full-detail reveal.
- Risk: responsive conversion introduces interaction regressions.
  - Mitigation: manual viewport QA and contract tests.
- Risk: preserving monolithic `App.tsx` increases implementation complexity.
  - Mitigation: make contained surface-level UI edits with strict regression checks.
