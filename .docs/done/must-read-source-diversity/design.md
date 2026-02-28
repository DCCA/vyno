# Design: Must-read Source Diversity Cap

## Selection Update
- Add `must_read_max_per_source` to profile configuration (default `2`).
- In selection pipeline:
  - iterate ranked non-video items
  - bucket source by family/domain (for example all arXiv feeds -> `arxiv.org`)
  - accept items while source-family count < cap
  - once pass completes, backfill from remaining ranked items until 5 Must-read entries

## Compatibility
- Keep ranking and scoring unchanged.
- Keep skim/videos composition unchanged except for excluding chosen Must-read ids.
- Preserve final section count limits.

## Verification
- Unit test for per-source cap behavior.
- Regression test suite pass.
