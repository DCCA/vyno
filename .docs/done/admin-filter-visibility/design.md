# Design: Admin Filter Visibility

## Approach
- Compute filter counters inside `run_digest` with low-overhead list counting.
- Keep existing pipeline behavior unchanged; only add telemetry.
- Publish counters into the existing `context_payload` object consumed by renderers.

## Runtime Metrics
- Add aggregate `filtering` block:
  - `dedupe_dropped`, `dedupe_dropped_videos`
  - `window_dropped`, `window_dropped_videos`
  - `seen_dropped`, `seen_dropped_videos`
  - `seen_readded`, `seen_readded_videos`
  - `blocked_dropped`, `blocked_dropped_videos`
  - `github_low_impact_dropped`
  - `ranking_dropped`, `ranking_dropped_videos`
- Add `video_funnel` block:
  - `fetched`, `post_window`, `post_seen`, `post_block`, `selected`

## Rendering
- Extend Telegram context lines with:
  - dropped stage summary
  - video funnel summary
- Extend Obsidian context lines with:
  - dropped stage summary
  - video funnel summary

## Testing
- Runtime integration assertions for `filtering` and `video_funnel` presence and values.
- Renderer assertions for new context lines.
- Full suite validation via existing `make test`.

## Risks
- Counter interpretation can be confusing if operators expect per-item reasons.
- Counts are run-level aggregates only.

## Mitigations
- Keep line labels explicit by stage name.
- Preserve existing context lines for continuity.
