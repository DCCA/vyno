# Design: Scoring Cache and Source Quality Filters

## Runtime Flow Changes
- Compute rule scores for all eligible items first for deterministic ranking and fallback reuse.
- Select top `max_agent_items_per_run` item IDs for agent scoring.
- For selected items, check score cache by `(item.hash, openai_model)` with 24h TTL.
- Use cached scores when valid; otherwise call agent scorer with retries.
- Use rules fallback for agent failures and cap-overflow items.

## Coverage and Telemetry
- Coverage denominator is the number of items selected for agent scoring (post-cap).
- Cap-overflow items are tracked as policy fallback, not error fallback.
- Emit run telemetry for:
  - `agent_scope_count`
  - `cache_hits`
  - `cache_misses`
  - `policy_fallback_count`
  - `fallback_reasons`

## Storage Changes
- Add `score_cache` table in SQLite with primary key `(item_hash, model)`.
- Persist score fields and tag metadata aligned with `scores` table.
- Provide store helpers to load and upsert cache entries.

## GitHub Quality Filtering
- Extend GitHub fetch options to support recency windows:
  - `repo_max_age_days` for repo update-style items
  - `activity_max_age_days` for releases/issues/PRs
- Apply `min_stars`, `include_forks`, and `include_archived` filters where API payload supports it.

## X Inbox Quality Filtering
- Normalize `twitter.com` and `x.com` URLs to canonical `https://x.com/<handle>/status/<id>`.
- Deduplicate by canonical URL.
- Ignore comment suffixes that match low-signal promotional patterns.
