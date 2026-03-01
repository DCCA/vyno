# Completion Summary: ui-loading-affordances

## What changed
- Added explicit loading-state typing and tracking for setup/manage actions in `web/src/App.tsx`.
- Added a global loading banner with contextual text (for example, `Running onboarding preview...`).
- Restored/added in-button loading feedback and labels for refresh, source mutations, source-pack apply, review actions, and rollback.
- Ensured Digest Activity is visible even before granular progress arrives, with fallback status text (`Digest run in progress. Waiting for progress details...`).

## Verification
- `npm --prefix web run build` passed.
- `make test` passed.
- Browser check confirmed loading text appears during preview execution.
