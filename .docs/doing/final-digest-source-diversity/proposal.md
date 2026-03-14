# Proposal: Final Digest Source Diversity

## Why
Recent delivered digests can still end up dominated by a single source family even though the initial selector applies source caps. The source-diversity invariant is lost during Must-read quality repair, which rebuilds the final digest from the ranked pool without reapplying the cap.

## Scope
- Preserve source-diversity caps after quality repair.
- Add a bounded research-heavy penalty so arXiv can surface without dominating.
- Improve run observability so final source-family concentration is visible.

## Out of Scope
- New user-facing diversity controls.
- Per-source custom weighting beyond the bounded research-heavy adjustment.
