# Proposal: high-impact-github-issues

## Why
The digest currently includes too many narrow GitHub issue threads in high-visibility sections. This reduces signal for strategic content prioritization.

## Scope
- Filter `github_issue` items before scoring/selection.
- Keep only issues that match: trusted org + medium-severity keyword.
- Add telemetry and tests for the filter behavior.

## Out of scope
- Filtering `github_pr` items.
- Reworking section renderer formats.
