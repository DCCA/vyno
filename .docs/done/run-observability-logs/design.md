# Design: Run Observability Logs

## Approach
Use Python's built-in logging with a rotating file handler and JSON formatter.

## Log Format
Each event is one JSON line with these base fields:
- `ts`
- `level`
- `run_id`
- `stage`
- `message`

Additional event-specific fields are appended (for example `source`, `item_count`, `status`, `error`).

## Configuration
Environment variables:
- `DIGEST_LOG_PATH` (default `logs/digest.log`)
- `DIGEST_LOG_LEVEL` (default `INFO`)
- `DIGEST_LOG_MAX_BYTES` (default `5000000`)
- `DIGEST_LOG_BACKUP_COUNT` (default `5`)

## Integration Points
- CLI startup initializes logging once.
- Runtime emits stage events and error events.
- Makefile provides `make logs` to tail log output.

## Tradeoffs
- File-based logs are simple and local-first.
- No external aggregation in MVP; operators inspect local files.
