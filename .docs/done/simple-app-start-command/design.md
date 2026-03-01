# Design: Simple App Start Command

## Approach
- Add `scripts/start-app.sh` as the orchestrator.
- Add `make app` target that runs this script.

## Script behavior
1. Verify required tools (`curl`, `npm`, and either `uv` or `bin/digest`).
2. Ensure runtime directories exist (`logs`, `.runtime`).
3. Optionally install UI dependencies when `web/node_modules` is missing.
4. Start API in background using `make web-api`.
5. Poll API health endpoint (`/api/health`) until ready.
6. Start UI in foreground (`npm --prefix web run dev -- --host 127.0.0.1 --port 5173`).
7. Trap exit signals and stop API child process.

## Why this shape
- Keeps existing Make targets intact.
- Uses shell orchestration for minimal blast radius.
- Makes startup friendly while preserving advanced workflows.
