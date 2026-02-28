# Proposal: incremental-video-presence

## Why
After switching web live runs to incremental mode, digests can legitimately contain zero videos when no YouTube items are new, even if recent video items exist in the current window.

## Scope
- Preserve incremental behavior.
- Add a narrow supplement rule: when incremental candidate set has no videos, add a small number of seen video candidates from the same window.

## Out of scope
- Broad fallback to all seen items.
- Changes to source connectors.
