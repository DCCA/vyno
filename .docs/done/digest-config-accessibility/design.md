# Design: Digest Configuration Accessibility

## Mode Model
Expose four user-facing modes:
- `Fresh Only`: `use_last_completed_window=true`, `only_new=true`, `allow_seen_fallback=false`
- `Balanced` (recommended): `use_last_completed_window=true`, `only_new=true`, `allow_seen_fallback=true`
- `Replay Recent`: `use_last_completed_window=true`, `only_new=false`
- `Backfill` (advanced): `use_last_completed_window=false`, `only_new=false`

## Configuration Persistence
Persist default run policy in profile overlay under a new section:
- `run_policy.default_mode`
- `run_policy.allow_run_override`
- `run_policy.seen_reset_guard` (confirmation policy)

If the section is absent, resolve to current Web defaults for compatibility.

## API Changes
- Extend `POST /api/run-now` to accept optional payload:
  - `mode` (one-time override)
- Add run policy endpoints:
  - `GET /api/config/run-policy`
  - `POST /api/config/run-policy`
- Add seen maintenance endpoints:
  - `POST /api/seen/reset/preview`
  - `POST /api/seen/reset/apply`

## Strictness Computation
Compute per-run strictness from existing run context counters:
- Inputs: `fetched`, `post_window`, `post_seen`, `post_block`, `selected`
- Derive stage drop ratios and an aggregate strictness score.
- Map score to levels:
  - `Low`, `Medium`, `High`

Emit:
- strictness level + score
- top restriction reasons (ordered by contribution)
- actionable suggestions based on dominant drop stage(s)

## Web UX
Add a new `Digest Policy` panel in Manage Workspace:
- Default mode selector
- Seen behavior explanation text
- Run-once override on `Run now`
- Seen maintenance controls with dry-run preview + confirmation

Add strictness section in run review/timeline:
- strictness badge
- filter funnel visualization
- top reasons
- suggested actions

## Safety & Audit
- Require explicit confirmation for destructive seen reset.
- Log all policy mutations and reset actions in admin audit trail.
- Include actor and scope metadata in audit details.

## Verification
- Unit tests for mode mapping and strictness derivation.
- API tests for run-policy and seen-maintenance endpoints.
- UI tests for mode controls and strictness rendering.
- Regression tests for default behavior continuity.
