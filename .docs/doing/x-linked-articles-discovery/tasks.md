# Tasks: X Linked Articles Discovery

- [x] 1. Extend X selector ingestion
- [x] 1.1 Promote outbound links from `x_author` posts into `link` items
- [x] 1.2 Keep `x_theme` results post-only in v1
- [x] 1.3 Use preview metadata as best-effort enrichment for promoted links

- [x] 2. Merge duplicate discovery context
- [x] 2.1 Merge same-URL items during exact dedupe instead of dropping later duplicates
- [x] 2.2 Preserve X endorsement markers when duplicates merge

- [x] 3. Score and verify endorsed articles
- [x] 3.1 Boost promoted links using unique X endorsement markers
- [x] 3.2 Add or update tests for selector promotion, dedupe merging, and endorsement-aware scoring
- [x] 3.3 Run backend and frontend verification and sync docs status
