# Completion Summary: Web Timeline Observability

## What Changed
- Added persisted timeline events and notes in SQLite:
  - `run_timeline_events`
  - `run_timeline_notes`
- Added timeline store APIs for:
  - event insert/list with filters
  - run list
  - run summary
  - notes add/list
- Wired Web run progress handlers to persist timeline events during and after runs.
- Added Web API endpoints:
  - `GET /api/timeline/runs`
  - `GET /api/timeline/events`
  - `GET /api/timeline/live`
  - `GET /api/timeline/summary`
  - `GET /api/timeline/notes`
  - `POST /api/timeline/notes`
  - `GET /api/timeline/export`
- Added a Timeline tab in Web admin with:
  - run selector
  - stage/severity filters
  - newest/oldest ordering
  - live polling pause/resume
  - summary badges
  - events table
  - event detail inspector
  - review notes capture/list
  - JSON export action
  - active-run polling refresh

## Verification
- `npm --prefix web run build` passed.
- `make test` passed (`127` tests).

## Risks / Follow-Ups
- Polling-based refresh is sufficient for MVP but can be upgraded to SSE/WebSocket for high-frequency event streams.
- Note fields currently include basic author/note content; labels/actions are stored backend-side and can be exposed in UI controls later.
