# Design: Onboarding Setup Flow

## Architecture Deltas
- Reuse existing web API in `src/digest/web/app.py` and add onboarding endpoints.
- Add onboarding domain module `src/digest/ops/onboarding.py` for:
  - preflight checks
  - onboarding state persistence
  - source pack catalog/apply
  - derived onboarding status
- Extend runtime execution with preview mode in `run_digest`.
- Extend CLI with `doctor` command in `src/digest/cli.py`.
- Extend web UI `web/src/App.tsx` with an `Onboarding` tab.

## API Additions
- `GET /api/onboarding/preflight`
- `GET /api/onboarding/status`
- `GET /api/onboarding/source-packs`
- `POST /api/onboarding/source-packs/apply`
- `POST /api/onboarding/preview`
- `POST /api/onboarding/activate`

## Preflight Checks
- Config parsing:
  - effective sources (base + overlay)
  - effective profile (base + overlay)
- Filesystem readiness:
  - overlay paths writable
  - DB path writable/creatable
  - runtime state paths writable
- Secret and integration checks:
  - OpenAI key required when LLM/agent/quality-repair is enabled
  - GitHub token warning for GitHub source usage
  - output readiness (Telegram/Obsidian)
  - optional DNS resolution hints for provider hosts

## Safe Preview Strategy
- Execute preview with:
  - temporary SQLite DB under `.runtime/preview/`
  - `run_digest(..., preview_mode=True)`
- In preview mode runtime MUST:
  - skip Telegram delivery
  - skip Obsidian file writes
  - skip latest Telegram runtime artifact write
- Return preview artifacts directly in API response.

## Onboarding State
- Persist state in `.runtime/onboarding-state.json`.
- Store step completion timestamps and optional details.
- Step completion is updated by:
  - preflight success
  - source pack/source mutation
  - profile save
  - preview run
  - activation trigger

## UI Flow
1. Step tracker card with completion badges.
2. Preflight panel with pass/warn/fail checks.
3. Source packs panel with one-click apply.
4. Preview + activate panel with returned artifacts.
5. Existing tabs remain for advanced editing.

## Safety and Rollback
- Source pack application reuses existing source overlay mutation path.
- Mutating actions continue to emit config snapshots for rollback.
- Activation and run-now continue to use run lock semantics.
