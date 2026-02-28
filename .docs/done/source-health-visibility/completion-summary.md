# Completion Summary: source-health-visibility

## What Changed
- Added structured source error visibility in API responses.
- Added recent-run source health aggregation endpoint.
- Added web UI panel listing failing sources with recommended fixes.
- Added parser tests for common failure patterns (RSS timeout, GitHub 403).

## Verification
- `make test` passed.
- `npm --prefix web run build` passed.
