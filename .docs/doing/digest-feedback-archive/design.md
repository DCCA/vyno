# Design: Digest Feedback Archive

## Backend
- Extend `ProfileConfig` with `content_depth_preference` and validate accepted values in config parsing.
- Add `technicality_level()` and `content_depth_adjustment()` in rule scoring, then apply the adjustment during runtime ranking.
- Extend selection with `digest_max_per_source` so `must_read + skim` share a digest-wide source-family cap.
- Persist per-run selected items in `run_selected_items`.
- Persist per-run delivery artifact metadata in `run_artifacts`, with file content stored under `.runtime/run-artifacts/<run_id>/`.
- Extend feedback storage to capture target kind, target key, actor, and a serialized feature payload for future bias calculations.

## API
- Add run archive endpoints for selected items and delivered artifacts.
- Add feedback endpoints for item-level and source-level actions.
- Add a feedback summary endpoint for UI explainability.

## UI
- `Timeline`: review archived Telegram/Obsidian payloads and submit per-item feedback.
- `Sources`: submit source-level preference actions from each source card.
- `Profile`: set baseline technical depth and display a compact personalization summary.

## Compatibility
- Keep existing timeline endpoints, preview mode, and core run flow intact.
- Make archive persistence additive; older runs without archived artifacts still load safely.
- Keep ranking changes conservative by default to avoid abrupt digest shifts.
