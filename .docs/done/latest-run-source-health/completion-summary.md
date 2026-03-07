# Completion Summary: latest-run-source-health

## Delivered
- Changed `/api/source-health` in `src/digest/web/app.py` to report only source errors from the latest completed run.
- Cleared stale source-health alerts automatically when a newer completed run has no source errors.
- Kept the existing source-health API response shape so the current UI success/healthy rendering continued to work unchanged.
- Aggregated duplicate source errors for the same source within a single run into one item with an incremented count.
- Added backend regression tests covering latest-run scoping, stale-alert clearing, duplicate aggregation, and no-completed-run behavior.

## Verification
- `python3 -m unittest tests.test_web_source_health -v` passed.
- `make test` passed (`153` tests).

## Notes
- No frontend code changes were required because the UI already derives green/healthy state from an empty `sourceHealth` payload.
