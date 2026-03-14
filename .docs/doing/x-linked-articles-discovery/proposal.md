# Proposal: X Linked Articles Discovery

## Why
- The product already ingests `x_author` and `x_theme` selectors, but it only treats the resulting X posts as digest items.
- Many high-signal AI links are discovered on X before they appear in RSS or other feeds.
- Operators want the digest to capture that higher-quality article discovery path without flooding the digest with low-value social posts.

## Scope
- Promote outbound links from `x_author` posts into first-class digest candidates.
- Keep X-native posts as valid candidates.
- Merge duplicate URLs discovered through X and non-X sources so X endorsements strengthen article ranking instead of creating duplicates.

## Non-Goals
- Promoting links from `x_theme` in v1.
- Scraping X outside the current API path.
- Full article-body extraction.
