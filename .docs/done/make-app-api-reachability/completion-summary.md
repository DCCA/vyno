# Completion Summary

## What Changed
- Hardened `scripts/start-app.sh` so it fails immediately when the configured API or UI port is already occupied.
- Stopped forcing `VITE_API_BASE` during local dev startup unless it is explicitly provided, which makes the browser use relative `/api` requests through the existing Vite proxy.
- Added a frontend source-shape regression test covering the proxied API path and launcher port guards.

## Validation
- `sh -n scripts/start-app.sh`
- `npm --prefix web run test`
- `npm --prefix web run build`
- Real startup verification outside the sandbox:
  - confirmed `./scripts/start-app.sh` now exits early with `API port 8787 is already in use` when that conflict exists
  - confirmed a clean run on alternate ports served `GET /api/config/source-types` through the UI proxy with HTTP `200`

## Risks
- This change improves local dev boot behavior but does not add background process management; if users intentionally want multiple concurrent app instances, they still need distinct ports.
- Production environments that set `VITE_API_BASE` explicitly are unchanged and should continue to work.

## Follow-Up
- If fetch errors still appear on a user machine after this change, check for stale local listeners on `5173` or `8787` first because the launcher will now surface those conflicts directly.
