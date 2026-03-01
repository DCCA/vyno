# Proposal: Admin Filter Visibility

## Why
Operators need to understand why expected content, especially videos, does not appear in a digest run. Current run context reports fetched and selected totals, but does not clearly break down where items are filtered out.

## Scope
- Add per-stage filter accounting to digest run context.
- Expose video-specific funnel counts from fetch to final selection.
- Render filter breakdown in Telegram and Obsidian context sections.
- Add regression tests for runtime context and render outputs.

## Out of Scope
- Per-item rejection logs in output notes/messages.
- New persistence tables for filter telemetry history.
- Changes to ranking/scoring policy behavior.

