# Design: digest-context-feedback

## Data model
- Add optional `context` payload to `RunReport` with run funnel metrics:
  - fetch totals by source family
  - normalization and candidate counts
  - issue gate drop counts
  - final section sizes

## Runtime
- Build context snapshot in `run_digest()` using existing counters.
- Pass context into renderers and include in `RunReport`.

## Rendering
- Obsidian: add `## Context` section with compact bullet summary.
- Telegram: add a compact `Context` block after title.
- Include sparse-run sentence when final item count is low.

## Testing
- Renderer tests assert context presence and sparse explanation.
- Runtime integration test asserts report context fields are populated and coherent.
