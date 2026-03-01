# Design: X Follow People + Theme Ingestion

## Brownfield Delta Overview
Current state:
- `SourceConfig` supports `x_inbox_path` only.
- `source_registry` supports rss/youtube/github types only.
- `connectors/x_inbox.py` parses manual post URLs.

Proposed delta:
- Add selector source types: `x_author`, `x_theme`.
- Add provider router for X fetching.
- Add selector cursor state in SQLite.
- Keep inbox path as compatible fallback path.

## Architecture Changes

### 1. Source Configuration and Registry
- Extend `SourceConfig` in `config.py`:
  - `x_authors: list[str] = []`
  - `x_themes: list[str] = []`
- Extend source registry mappings (`ops/source_registry.py`):
  - `x_author -> x_authors`
  - `x_theme -> x_themes`
- Canonicalization rules:
  - `x_author`: normalize `@handle` -> `handle`, lowercase, validate token length/charset.
  - `x_theme`: whitespace-normalized query string, min length guard.

### 2. Provider Abstraction
Create provider router in `connectors/x_provider.py`:
- interface:
  - `fetch_author_posts(author: str, cursor: str | None, limit: int) -> FetchBatch`
  - `fetch_theme_posts(query: str, cursor: str | None, limit: int) -> FetchBatch`
- provider modes:
  - `inbox_only` (default compatibility mode)
  - `x_api` (official API mode)
- configuration:
  - env `DIGEST_X_PROVIDER=inbox_only|x_api`
  - env `X_BEARER_TOKEN` for API mode

### 3. Cursor State in SQLite
Add table in `storage/sqlite_store.py`:
- `x_selector_cursors(selector_type TEXT, selector_value TEXT, cursor TEXT, last_item_id TEXT, updated_at TEXT, PRIMARY KEY(selector_type, selector_value))`

Add methods:
- `get_x_cursor(selector_type, selector_value) -> str | None`
- `set_x_cursor(selector_type, selector_value, cursor, last_item_id) -> None`

### 4. X Selector Connector
Add `connectors/x_selectors.py`:
- loads effective `x_authors` and `x_themes`
- fetches per selector using provider router + cursor
- normalizes to `Item(type="x_post")`
- tags item raw_text/description with selector context (`author:`/`theme:`)
- emits source errors with prefixes:
  - `x_author:<selector>: <error>`
  - `x_theme:<selector>: <error>`

### 5. Runtime Integration
- In runtime fetch stage, execute:
  - `x_inbox` fetch (existing)
  - `x_selector` fetch (new; if selectors configured)
- Merge both result sets before downstream normalize/score/select.

### 6. Web and Bot Control Surfaces
- Existing source APIs remain; they automatically expose new source types through `supported_source_types()`.
- Web UI source type select receives `x_author` and `x_theme` options without introducing a new endpoint contract.
- Telegram `/source` add/remove/list and source wizard gain new selector types via same registry extension.

### 7. Source Health Mapping
- Extend `_parse_source_error` in web app to recognize:
  - `x_author:` and `x_theme:` prefixes.
- Add hints:
  - auth missing/invalid token
  - rate limit/backoff guidance
  - selector syntax remediation

## API Mode Details (v1)
- Author path:
  - resolve username -> user id (cached in memory during run)
  - fetch user posts with bounded recent count
- Theme path:
  - query recent posts by theme terms
  - include URL expansions when available
- Rate controls:
  - profile/env caps for max requests and max items per selector per run

## Data and Compatibility Notes
- Existing `seen` key dedupe remains final safety net.
- Existing `trusted_authors_x` and `blocked_authors_x` remain profile-level ranking/filter controls.
- Existing `x_inbox_path` remains valid and can coexist with selectors.

## Risks and Mitigations
- Risk: X API availability and rate limits vary.
  - Mitigation: provider mode flag + bounded fetch + clear source health hints.
- Risk: selector query noise.
  - Mitigation: min query length + scoring filters + optional profile exclusions.
- Risk: schema migration complexity.
  - Mitigation: additive SQLite table with idempotent creation.

## Verification Strategy
- Unit tests:
  - source canonicalization for `x_author`/`x_theme`
  - selector fetch normalization
  - cursor read/write behavior
- Integration tests:
  - mixed inbox + selector run path
  - source health error parsing and hints
  - web API source mutation with new types
- UI tests:
  - source type options include new selector types
  - add/remove/list works in sources workspace
