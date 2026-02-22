# Completion Summary: Run Observability Logs

## What Changed
- Added structured JSON logging with rotating file handler in `src/digest/logging_utils.py`.
- Added environment-driven logging config:
  - `DIGEST_LOG_PATH`
  - `DIGEST_LOG_LEVEL`
  - `DIGEST_LOG_MAX_BYTES`
  - `DIGEST_LOG_BACKUP_COUNT`
- Initialized logging in CLI startup.
- Added run-scoped stage logging in runtime:
  - `run_start`, fetch stages, normalization/selection/scoring, delivery stages, `run_finish`.
- Added `make logs` target to tail logs.
- Updated README to document `uv` workflow and logging commands.

## Verification
- `make test` -> PASS (21 tests)
- `make live` (network-enabled) -> PASS (`status=success`)
- `logs/digest.log` contains run-scoped structured events with stage and context fields.

## Risks
- Logs may contain operational metadata; ensure file permissions are appropriate.
- Very verbose source sets can increase log volume; rotation controls mitigate this.

## Follow-ups
- Optional: add redaction for sensitive fields if future events include secrets.
- Optional: add summary log event with section sizes (`must_read`, `skim`, `videos`).
