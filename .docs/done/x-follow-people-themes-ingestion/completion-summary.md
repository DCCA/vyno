# Completion Summary: X Follow People + Theme Ingestion

## What Changed
- Added new X selector source types:
  - `x_author`
  - `x_theme`
- Extended source config and overlay registry plumbing for selector-based X ingestion.
- Added X provider abstraction:
  - `inbox_only` (default compatibility mode)
  - `x_api` (official API-backed mode requiring `X_BEARER_TOKEN`)
- Added selector connector that:
  - fetches author/theme posts
  - normalizes to existing `Item(type="x_post")`
  - records per-selector source errors
  - persists selector cursor state
- Added SQLite cursor persistence table and methods (`x_selector_cursors`).
- Integrated selector ingestion in runtime while preserving inbox ingestion.
- Extended web source health parsing/hints for `x_author` and `x_theme` failures.
- Extended effective config payload and fetch-target counting to include selector sources.
- Updated README and default `config/sources.yaml` for new fields/env vars.

## Verification
- Backend test suite: `make test` passed.
- Frontend test suite: `npm --prefix web run test` passed.

## Compatibility Notes
- Existing `x_inbox_path` behavior is unchanged.
- Selector ingestion requires `DIGEST_X_PROVIDER=x_api` and valid `X_BEARER_TOKEN`.
- Without API mode, selector fetch emits explicit source-health errors while other sources continue.

## Follow-Ups
- Add provider capability discovery endpoint in web UI for proactive setup warnings.
- Add optional full-archive mode gating if project tier supports it.
