# Completion Summary: must-read-source-diversity

## What Changed
- Added configurable `must_read_max_per_source` to profile config.
- Updated section selection to enforce per-source cap in Must-read and backfill safely.
- Updated runtime wiring, default profile, README, and tests.

## Verification
- `make test` passed (full suite).

## Follow-ups
- If source balance is still skewed, add optional source-family weighting before selection.
