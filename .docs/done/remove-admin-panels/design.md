# Design: Remove Admin Panels

## Approach
- Delete panel modules instead of deprecating in place.
- Remove panel command wiring from `digest.cli`.
- Remove panel runtime dependencies from project manifests and lockfile.
- Remove panel-only tests and runbook/docs references.

## Compatibility Notes
- Existing CLI digest workflows (`run`, `schedule`, `bot`) remain unchanged.
- Telegram admin command workflows remain the primary remote operations path.

## Verification
- Run full unit/integration suite after removal.
- Confirm no references to removed commands in key docs and build scripts.
