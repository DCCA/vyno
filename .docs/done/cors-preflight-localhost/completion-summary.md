# Completion Summary: cors-preflight-localhost

## What changed
- Updated CORS configuration in `src/digest/web/app.py` to support dynamic localhost/private-network origins via `allow_origin_regex`.
- Added CORS helper functions:
  - `_cors_allowed_origins()` with optional `DIGEST_WEB_CORS_ORIGINS` override
  - `_cors_allow_origin_regex()` with optional `DIGEST_WEB_CORS_ORIGIN_REGEX` override
- Kept existing explicit known local origins as defaults.
- Added regression tests in `tests/test_web_cors.py` covering:
  - allowed/blocked origin matching
  - env override behavior
  - middleware wiring to accept alternate localhost ports

## Verification
- `make test` passed (`119` tests).
- Manual preflight check passed:
  - `OPTIONS /api/run-status` with origin `http://127.0.0.1:5174` returned `200` and `access-control-allow-origin` header.

## User impact
- Fixes browser `TypeError: Failed to fetch` failures caused by CORS preflight `400` when the frontend runs on alternate local ports.
