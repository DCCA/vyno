# Design: Telegram Layout Readability

## Approach
- Keep the current flat top-10 Telegram digest.
- Change each item block from a 2-line layout to a 3-line layout:
  - linked title
  - italic metadata line
  - concise summary line
- Reuse existing `ScoredItem` data for source, score, and section labels.

## Defaults
- Score tiers:
  - `High` for `>= 70`
  - `Medium` for `40–69`
  - `Low` for `< 40`
- Metadata order:
  - `Source · Section · Score`
- Common source aliases:
  - `arxiv.org` and `export.arxiv.org` → `arXiv`
  - `news.ycombinator.com` → `Hacker News`
  - `simonwillison.net` → `Simon Willison`
  - `youtube.com` → `YouTube`

## Notes
- The redesign changes presentation only, not selection.
- Summary length should be tightened to keep metadata-rich blocks chunk-safe.
