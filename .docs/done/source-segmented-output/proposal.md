# Proposal: Source-Segmented Output

## Why
Mixing all sources into the same digest sections reduces scanability and makes source-specific tracking harder.

## Scope
- Add `output.render_mode` with `sectioned` and `source_segmented` modes.
- Add source-bucket rendering in Telegram and Obsidian.
- Keep existing sectioned output as default.

## Out of Scope
- Score/ranking policy changes.
- New source connectors.
