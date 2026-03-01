# Design: Web Timeline Observability

## Architecture
- Use SQLite as source-of-truth for timeline persistence.
- Capture timeline events from Web run progress handlers (`_record_run_progress` and terminal transitions).
- Keep existing in-memory run progress for lightweight status widgets.

## Data Model
### `run_timeline_events`
- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `run_id TEXT NOT NULL`
- `event_index INTEGER NOT NULL`
- `ts_utc TEXT NOT NULL`
- `stage TEXT NOT NULL`
- `severity TEXT NOT NULL` (`info|warn|error`)
- `message TEXT NOT NULL`
- `elapsed_s REAL NOT NULL`
- `details_json TEXT NOT NULL`

Indexes:
- `(run_id, event_index)`
- `(run_id, stage)`
- `(run_id, severity)`

### `run_timeline_notes`
- `id INTEGER PRIMARY KEY AUTOINCREMENT`
- `run_id TEXT NOT NULL`
- `created_at_utc TEXT NOT NULL`
- `author TEXT`
- `note TEXT NOT NULL`
- `labels_json TEXT`
- `actions_json TEXT`

Index:
- `(run_id, created_at_utc DESC)`

## Backend APIs
- `GET /api/timeline/runs?limit=N`
- `GET /api/timeline/events?run_id=...&limit=...&after_event_index=...&stage=...&severity=...&order=asc|desc`
- `GET /api/timeline/summary?run_id=...`
- `GET /api/timeline/notes?run_id=...`
- `POST /api/timeline/notes`
- `GET /api/timeline/export?run_id=...`

## UI Design
- Add `Timeline` as a Manage Workspace tab.
- Controls:
  - run selector
  - stage filter
  - severity filter
  - order selector (newest-first / oldest-first)
  - live polling pause/resume
  - refresh button
  - export JSON button
- Content:
  - summary badges/cards
  - event table (timestamp, stage, severity, message, elapsed)
  - event detail inspector (structured `details` payload)
  - notes list + add note form
- Live behavior:
  - polling-based refresh while run is active

## Comparable Product Alignment
- Temporal-style timeline controls:
  - newest/oldest event ordering
  - operator pause/resume of live updates
- Dagster/Airflow-style run inspection:
  - run-scoped event history with stage/severity filtering
  - summary + detailed event drilldown
- GitHub Actions-style postmortem workflow:
  - exportable run timeline payload for offline review
  - notes captured per run for follow-up actions

## Verification
- Unit tests for SQLite timeline persistence and filtered queries.
- API behavior tests via route endpoint invocation.
- Frontend build passes and backend test suite passes.
