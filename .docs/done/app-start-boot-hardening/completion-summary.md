# Completion Summary: app-start-boot-hardening

## Delivered
- Hardened `scripts/start-app.sh` to verify the web install is actually usable before skipping dependency installation.
- Added an explicit `node` requirement because the dependency health check and Vite startup both depend on it.
- Defaulted `UV_CACHE_DIR` into `.runtime/uv-cache` so `uv run digest` no longer relies on a permission-sensitive home cache path.
- Kept the launcher behavior unchanged when dependencies and cache paths are already healthy.

## Verification
- `sh -n scripts/start-app.sh` passed.
- `npm --prefix web run build` passed.
- `HOME=/tmp UV_CACHE_DIR=/tmp/uv-cache uv run digest --help` passed.

## Notes
- Full `make app` end-to-end startup could not be verified in the sandbox because local port binding fails in this environment even on alternate ports.
- The change specifically addresses the two reproduced launcher-side failures: incomplete `web/node_modules` state and unusable default `uv` cache path.
