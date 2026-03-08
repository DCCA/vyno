# Design

## Approach
- Keep the upstream `DigestSections` contract unchanged.
- Replace Telegram's current `must_read`-only primary selector with a renderer-local selector that consumes `must_read + skim + videos`.
- Use two passes over the already-selected pool:
  - Pass 1: choose the first occurrence of each source bucket until the target source count is met or the pool is exhausted.
  - Pass 2: fill remaining slots in existing order until the target item count is met.

## Constants
- `TELEGRAM_PRIMARY_MIN_ITEMS = 10`
- `TELEGRAM_PRIMARY_MIN_SOURCES = 5`

## Source Diversity
- Normalize source buckets locally in the Telegram renderer using the same host/token logic as pipeline selection:
  - GitHub-prefixed sources collapse to `github`
  - URLs collapse to host without `www.`
  - Other values are used as-is

## Verification
- Add renderer tests for:
  - 10-item backfill from `skim`
  - promotion of additional sources over duplicate-source items
  - fewer-than-10 selected items using all available items
- Run `make test`
