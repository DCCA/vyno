# Completion Summary

Rebalanced explicit trust inputs so source reputation becomes a soft ranking preference rather than a raw score boost, and made user-facing scores reflect the final adjusted ranking outcome.

## What Changed
- Removed raw trust boosts from rule scoring.
- Applied bounded post-score source preference in ranking.
- Persisted raw score, adjusted score, and adjustment breakdown for selected items.
- Updated Telegram, Timeline, and Profile wording to reflect adjusted-score and soft-preference semantics.

## Verification
- `make test`
- `npm --prefix web run test`
- `npm --prefix web run build`

## Risks / Follow-Ups
- Older archived runs still fall back to legacy raw-score display in operator review.
