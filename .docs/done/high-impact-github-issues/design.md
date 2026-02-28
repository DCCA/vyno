# Design: high-impact-github-issues

## Filtering approach
- Add a deterministic helper for `github_issue` impact in `src/digest/pipeline/github_issue_impact.py`.
- Rule: keep issue only if:
  - source owner belongs to `profile.trusted_orgs_github`
  - and issue text contains at least one medium-severity keyword.

## Runtime integration
- Apply filter to candidate items in `run_digest()` after existing seen/new candidate selection.
- Emit counters in candidate selection telemetry:
  - `github_issue_kept_high_impact`
  - `github_issue_dropped_low_impact`

## GitHub connector enrichment
- Enrich issue `raw_text` with labels and comments count to improve keyword matching quality.

## Tests
- Unit tests for issue impact classifier.
- Connector tests to verify issue metadata enrichment.
- Runtime integration test to verify gate behavior end-to-end.
