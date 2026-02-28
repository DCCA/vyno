# Proposal: Scoring Cache and Source Quality Filters

## Why
Digest runs can be slow and expensive when many items trigger agent scoring. Source inputs can also include low-signal GitHub and X items that reduce digest quality.

## Scope
- Add score caching keyed by item hash and model with a 24h TTL.
- Add `max_agent_items_per_run` cap and deterministic overflow fallback.
- Add stronger GitHub quality filters (stars and recency windows).
- Add X inbox sanity filters (URL normalization, dedupe, low-signal comment skip).
- Add telemetry and tests for cache/cap/filter behavior.

## Out of Scope
- Replacing SQLite with external storage.
- Reworking ranking formulas beyond cap/filter behavior.
- Introducing new ingestion providers.
