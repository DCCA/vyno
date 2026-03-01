# Completion Summary: simple-app-start-command

## What changed
- Added one-command local startup with `make app`.
- Added `scripts/start-app.sh` to orchestrate API + UI startup, health check, and shutdown cleanup.
- Updated `README.md` quick start, command list, and onboarding flow to use `make app` as the default friendly path.

## Verification
- Smoke tested startup: API health and UI HTTP endpoint both reachable after `make app`.
- Verified cleanup on interrupt (`INT`) and terminate (`TERM`) with no lingering API/UI listeners.

## Notes
- Existing advanced workflows (`make web-api`, `make web-ui`) remain available.
