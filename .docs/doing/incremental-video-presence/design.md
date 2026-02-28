# Design: incremental-video-presence

## Candidate selection adjustment
- In `run_digest()`, after unseen filtering in incremental mode:
  - if `allow_seen_fallback=false` and no candidate has `type == "video"`, select up to 2 seen video items from current window candidates.
  - sort supplements by recency (`published_at` desc) when available.
- Append supplements without enabling broad seen fallback.

## Observability
- Add `supplemental_seen_videos` to candidate-select log/progress payload.

## Tests
- Add runtime integration test proving incremental run can include video via targeted seen-video supplement.
