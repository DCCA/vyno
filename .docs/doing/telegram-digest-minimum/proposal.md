# Proposal

## Why
Telegram digests are currently too short because the renderer only emits `must_read`, which is capped at five items even when the run selected more items overall.

## Scope
- Expand Telegram digest rendering to target at least ten items.
- Promote source diversity in the Telegram-rendered item list.
- Keep upstream selection, profile schema, and non-Telegram outputs unchanged.
- Add renderer tests that lock the new behavior.

## Non-Goals
- Change Obsidian output.
- Change global digest selection limits or run-report counts.
- Introduce new profile knobs for this behavior.
