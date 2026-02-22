# Admin Panel Runbook

## Start
1. Set env vars:
- `ADMIN_PANEL_USER`
- `ADMIN_PANEL_PASSWORD`
2. Run panel:
- `make admin`
3. Open:
- `http://127.0.0.1:8787/admin/login`

## Core Operations
- Sources: `/admin/sources`
- Trigger run: `/admin/runs` -> `Run now`
- Bot control: `/admin/bot`
- Logs: `/admin/logs`
- Outputs: `/admin/outputs`
- Feedback: `/admin/feedback`

## Failure Recovery
- Bot appears running but unhealthy:
1. `/admin/bot` -> Stop
2. `/admin/bot` -> Start
- Run stuck due lock:
1. Verify in `/admin/runs` and logs
2. Remove stale lock file `.runtime/run.lock` only if no active process
3. Trigger run again
- Source mismatch:
1. Check effective sources in `/admin/sources`
2. Verify overlay file `data/sources.local.yaml`

## Audit
- Review recent admin actions in `/admin/feedback` (Admin Audit section).

