# SQLite Schema Module Extraction Proposal

## Why

`src/digest/storage/sqlite_store.py` mixes schema definition, migration helpers, and storage operations in one large module. The schema SQL is static and can move into its own module without changing storage behavior.

## Scope

- Move the SQLite schema SQL into `digest.storage.schema`.
- Keep `SQLiteStore._init_db` responsible for executing schema and legacy column checks.
- Verify timeline/store tests and full backend/security checks.

## Non-goals

- No schema changes.
- No migration behavior changes.
- No storage API changes.
