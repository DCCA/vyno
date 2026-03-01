# Design: Web API Secret Redaction and Authentication

## Authentication
- Add lightweight token middleware in `src/digest/web/app.py`.
- Config via env:
  - `DIGEST_WEB_API_AUTH_MODE` = `required|optional|off` (default `required`)
  - `DIGEST_WEB_API_TOKEN` = token value
  - `DIGEST_WEB_API_TOKEN_HEADER` = incoming header name (default `X-Digest-Api-Token`)
- Bypass auth for:
  - `OPTIONS` preflight
  - `/api/health`

## Secret Redaction
- Add recursive redaction utility for secret-like keys (token/secret/password/api key).
- Redact on outbound responses for profile/effective data.
- Redact snapshot payload fields before writing history files.

## Placeholder Rehydration
- Use a stable placeholder marker (for example `__REDACTED__`).
- For profile `validate/diff/save`, recursively replace marker values with current effective values before parsing.
- This preserves existing secrets when UI posts redacted values.

## Frontend/Startup
- Web UI API helper attaches auth header when `VITE_WEB_API_TOKEN` exists.
- `scripts/start-app.sh` sets a session token automatically when not provided and passes it to API/UI env vars.

## Verification
- Add unit tests for auth decision logic and redaction/rehydration helpers.
- Run full test suite and web build.
- Smoke test `make app` startup with authenticated UI requests.
