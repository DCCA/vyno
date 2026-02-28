# Completion Summary: high-impact-github-issues

## What changed
- Added deterministic GitHub issue impact gate in `src/digest/pipeline/github_issue_impact.py`.
- Runtime now filters `github_issue` candidates in `src/digest/runtime.py` to keep only issues that match:
  - trusted org (`trusted_orgs_github`)
  - and at least one medium-severity keyword.
- Added telemetry fields in candidate selection events:
  - `github_issue_kept_high_impact`
  - `github_issue_dropped_low_impact`
- Enriched GitHub issue connector payloads in `src/digest/connectors/github.py` with labels and comments metadata in `raw_text`.

## Verification
- `make test` passed (111 tests).
- `make web-ui-build` passed.

## Notes
- Scope intentionally applies only to `github_issue` items.
- `github_pr` behavior remains unchanged by this change set.
