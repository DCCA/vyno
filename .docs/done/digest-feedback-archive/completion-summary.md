# Completion Summary

Persisted delivered digest artifacts and selected-item history, then added item/source feedback so future runs can learn from explicit operator signals.

## What Changed
- Archived exact Telegram and Obsidian outputs for non-preview runs.
- Persisted selected items per run for Timeline digest review.
- Added item and source feedback APIs plus Timeline, Sources, and Profile feedback surfaces.
- Added content-depth controls and digest-wide source diversity support to the ranking path.

## Verification
- `make test`
- `npm --prefix web run test`
- `npm --prefix web run build`

## Risks / Follow-Ups
- Older runs from before artifact archiving are not backfilled with exact Telegram payloads.
