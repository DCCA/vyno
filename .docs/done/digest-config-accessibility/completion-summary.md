# Completion Summary: digest-config-accessibility

## What changed
- Added user-facing run policy controls with four digest modes (`fresh_only`, `balanced`, `replay_recent`, `backfill`) and persisted defaults under `run_policy`.
- Extended `POST /api/run-now` with one-time mode override support and added `GET/POST /api/config/run-policy` endpoints.
- Added seen-history maintenance endpoints with safety controls:
  - `POST /api/seen/reset/preview`
  - `POST /api/seen/reset/apply` with explicit confirmation and audit logging.
- Implemented timeline strictness transparency:
  - strictness score and level
  - filter funnel (`fetched -> post_window -> post_seen -> post_block -> selected`)
  - top restriction reasons
  - actionable recommendations.
- Added Web UI support for digest policy, run-now override, seen reset preview/apply, and timeline transparency.
- Added frontend contract tests in `web/tests/` using zero-dependency `node --test`.

## Verification
- `make test` passed (`134` tests).
- `npm --prefix web run build` passed.
- `npm --prefix web run test` passed (`2` tests).

## Risks / Follow-ups
- Frontend tests are contract-level source assertions; they do not exercise DOM behavior in a browser runner.
- Follow-up option: adopt a full frontend test harness (for example, Vitest + Testing Library) when network/dependency installation is available.
