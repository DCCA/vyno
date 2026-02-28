# Design: Source Health Visibility

## Backend
- Extend SQLite store with:
  - latest run detail retrieval (with raw error lines)
  - recent source-error run retrieval
- Parse raw source error lines into structured records:
  - `kind`, `source`, `error`, `hint`
- Add API endpoints:
  - enriched `/api/run-status` (latest completed run error details)
  - `/api/source-health` (aggregated recent failures)

## Frontend
- Add source health card near dashboard header.
- Display top failing sources with frequency, last error, and suggested fix.
- Keep periodic refresh aligned with run status polling.
