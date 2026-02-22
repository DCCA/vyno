# Proposal: Run Observability Logs

## Why
Run status in SQLite is useful, but diagnosis is slow without stage-level logs. We need structured logs to quickly identify where and why failures happen.

## Scope
- Add structured rotating file logs for run lifecycle and key pipeline stages.
- Include run-scoped correlation (`run_id`) in every event.
- Add simple operator command to tail logs.

## Out of Scope
- Changes to ranking policy or source coverage.
- External log shipping infrastructure.

## Success Conditions
- Every run writes start/finish events with `run_id`.
- Errors include stage + context in logs.
- Operators can tail logs with one command.
