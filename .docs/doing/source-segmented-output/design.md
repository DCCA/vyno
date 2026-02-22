# Design: Source-Segmented Output

## Approach
Add a shared source bucket utility and branch renderer line building by mode.

## Buckets
- GitHub
- Research & Articles
- Video
- X / Social
- Other

## Telegram
- Add source-segmented line builder with:
  - Top Highlights
  - non-empty source buckets
- Keep chunking behavior unchanged.

## Obsidian
- Add source-segmented note sections with:
  - Top Highlights
  - non-empty source buckets
- Reuse existing text cleanup and tag formatting.

## Runtime
Pass `profile.output.render_mode` into both Telegram and Obsidian renderers.
