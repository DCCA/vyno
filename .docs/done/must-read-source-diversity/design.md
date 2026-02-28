# Design: Must-read Source Diversity Cap

## Selection Update
- Add `must_read_max_per_source` to profile configuration (default `2`).
- In selection pipeline:
  - iterate ranked non-video items
  - accept items while source count < cap
  - once pass completes, backfill from remaining ranked items until 5 Must-read entries

## Compatibility
- Keep ranking and scoring unchanged.
- Keep skim/videos composition unchanged except for excluding chosen Must-read ids.
- Preserve final section count limits.

## Verification
- Unit test for per-source cap behavior.
- Regression test suite pass.
