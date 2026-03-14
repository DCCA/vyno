# Design: X Linked Articles Discovery

## Fetch Path
- Extend `x_selectors` so `x_author` posts still emit `x_post` items and also emit promoted `link` items for non-X outbound URLs.
- Use the existing link preview fetcher to obtain resolved URL, host, title, and description for promoted links.
- Fall back cleanly when preview fetch fails so link promotion is best-effort rather than run-blocking.

## Deduplication
- Replace exact-drop behavior with exact-merge behavior for same-URL items.
- Prefer article/link representations over `x_post` for duplicate URLs.
- Merge `raw_text` so endorsement markers survive even when the article candidate originated elsewhere first.

## Scoring
- Add an endorsement marker pattern in `raw_text` and count unique endorsing authors.
- Convert endorsement count into a bounded quality boost.
- Tag endorsed items as `x-discovered` for explainability and downstream review.
