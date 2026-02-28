# Completion Summary: online-mustread-quality-repair

## What Changed
- Added online Must-read quality judge + conditional repair in runtime.
- Added persisted quality evaluation records and cross-run learning priors.
- Added ranking offset application from decayed priors and feedback bias.
- Added runtime quality telemetry and tests covering apply/skip/fail-open/learning behavior.

## Verification
- `make test` passed with full suite coverage for quality-repair scenarios.

## Follow-ups
- Tune repair threshold and learning offsets using run_quality_eval trends.
