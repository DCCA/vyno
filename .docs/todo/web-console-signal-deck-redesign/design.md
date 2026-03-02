# Design: Web Console Signal Deck Redesign

## Architecture Impact
- Frontend only (`web/`), no backend contract changes.
- Reuse current API polling cadence and action handlers.
- Keep all existing state machines in `App.tsx` unless extraction improves readability with no behavior drift.

## UI Strategy

### 1. Information Framework
- Introduce a structured top band:
  - Run status ribbon
  - Critical counters (source errors, summary errors, active mode)
  - Primary CTA cluster (`Run now`, `Refresh`, contextual setup/manage action)
- Move dense data blocks below a clear summary layer.
- Convert long vertical stacks into grouped cards with explicit section headers and action slots.

### 2. Visual System
- Define CSS custom properties for:
  - typography scale
  - spacing rhythm
  - semantic status colors (`ok`, `warn`, `error`, `active`)
  - elevation/surface tokens
- Avoid generic color treatment; commit to a strong neutral base with sharp accent signals.
- Add subtle texture/gradient depth on page background to reduce flatness.
- Status affordances use color + iconography + text labels so severity is never color-only.
- Contrast checks are part of token finalization for text, badges, controls, and focus rings.

### 3. Typography
- Use a distinctive display face for page/surface titles.
- Use a high-legibility body face for dense data and forms.
- Tighten label/value contrast in cards and tables.

### 4. Motion Model
- Page-load stagger for top-level blocks.
- Deterministic loading animation patterns:
  - spinner + status text for blocking actions
  - skeleton strips for dense table placeholders
  - progress bar emphasis for live run activity
- Respect `prefers-reduced-motion`.

### 5. Responsive Behavior
- Desktop (`>=1200px`): multi-column composition with persistent context rail.
- Tablet (`768px-1199px`): condensed grid, stacked action rows, reduced chrome.
- Mobile (`<768px`): single-column flow, sticky primary actions, collapsible diagnostics.
- Touch ergonomics: primary controls and taps targets follow mobile-safe sizing and spacing.

### 6. Semantic and URL State Strategy
- Preserve semantic landmarks and heading structure in JSX (`main`, section headings, labeled regions).
- Keep critical forms explicitly labeled and keep helper/error text adjacent to fields.
- Persist primary surface context in URL query state when practical (surface/tab) without backend changes.

### 7. Stability and Performance
- Use skeletons sized to final card/table geometry to reduce cumulative layout shift.
- Keep transitions short and composited (`opacity/transform`) to avoid jank.
- Avoid heavy visual effects on low-power mobile paths; degrade gracefully.

## Key Surface Redesign Notes
- `Dashboard`: high-priority status summary first, then activity, then detailed health blocks.
- `Sources`: split into Overview / Effective / Health with clearer affordances and sticky filters.
- `Profile/Review`: improve diff readability via grouped sections and strong monospace contrast treatment.
- `Timeline`: event severity styling and note actions aligned into readable scan lanes.

## Risk Management
- Risk: visual refactor introduces behavior regressions.
  - Mitigation: preserve handler wiring first, style/layout changes second.
- Risk: responsive breakpoints regress dense tables.
  - Mitigation: explicit viewport QA with horizontal overflow checks.
- Risk: animation harms clarity/perf.
  - Mitigation: cap transition durations and avoid heavy JS animation dependencies unless needed.

## Verification Plan
- Run web tests and manual smoke checks for all surfaces.
- Validate loading state for each `saveAction` branch.
- Validate at representative widths (mobile/tablet/desktop).
- Capture before/after screenshots for review.
- Run contrast and keyboard-only audits on redesigned surfaces.
- Validate non-color status comprehension and touch-target usability in mobile QA.
- Validate URL restore behavior for primary surface context.
