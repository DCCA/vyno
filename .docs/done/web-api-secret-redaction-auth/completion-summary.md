# Completion Summary: web-api-secret-redaction-auth

## What changed
- Added token-based API auth enforcement for web API routes in `src/digest/web/app.py`.
  - Env controls:
    - `DIGEST_WEB_API_AUTH_MODE=required|optional|off` (default `required`)
    - `DIGEST_WEB_API_TOKEN`
    - `DIGEST_WEB_API_TOKEN_HEADER` (default `X-Digest-Api-Token`)
  - Health and CORS preflight remain accessible without auth.
- Added recursive secret redaction and placeholder rehydration utilities.
  - Redacts secret-like keys from profile/effective API responses.
  - Redacts profile data stored in config history snapshots.
  - Rehydrates redacted placeholders for `validate/diff/save` to preserve existing secrets.
- Updated UI API client to send auth header when configured (`VITE_WEB_API_TOKEN`, `VITE_WEB_API_TOKEN_HEADER`).
- Updated `scripts/start-app.sh` to auto-generate a session token for `make app` when required auth is enabled, and wire token to API/UI processes.
- Documented web API auth usage in `README.md` and `.env.example`.

## Verification
- Added tests in `tests/test_web_security.py` for auth decisions and redaction/rehydration behavior.
- `make test` passed (`124` tests).
- `npm --prefix web run build` passed.
- `make app` smoke test passed with startup + interrupt cleanup.
- Manual auth check verified:
  - `GET /api/config/profile` without token -> `401`
  - with valid token -> `200` and redacted token fields.
