# Web Security Helper Extraction Proposal

## Why

`src/digest/web/app.py` still holds the CORS, API-auth, and secret-redaction
helpers as a cohesive top-of-file block. They are pure, environment-driven
functions with their own configuration constants and no route or `create_app`
state, so they can move into a focused module — continuing the
helper-extraction pattern already applied for `feedback`, `schedule`,
`run_progress`, and `sources`.

## Scope

- Move the security helpers and their constants into a new
  `digest.web.security` module: `DEFAULT_WEB_CORS_ORIGINS`,
  `DEFAULT_WEB_CORS_ORIGIN_REGEX`, `DEFAULT_WEB_API_AUTH_MODE`,
  `DEFAULT_WEB_API_TOKEN_HEADER`, `ALLOWED_WEB_API_AUTH_MODES`,
  `REDACTED_SECRET`, `SECRET_KEY_RE`, plus `_cors_allowed_origins`,
  `_cors_allow_origin_regex`, `_web_api_auth_mode`, `_web_api_token`,
  `_web_api_token_header`, `_api_auth_decision`, `_is_secret_key`,
  `_redact_secrets`, and `_rehydrate_redacted_value`.
- Re-import the eight route-facing helpers into `digest.web.app` so the CORS
  middleware and auth middleware keep working. `_is_secret_key` and the
  non-route constants stay internal to `digest.web.security`.
- Update `test_web_security` and `test_web_cors` to import the security symbols
  from `digest.web.security` (their new owner).
- Verify security/CORS tests and the full backend/security checks.

## Non-goals

- No auth-decision, CORS, or redaction behavior changes.
- No API shape changes.
- No route or scheduler-loop changes.
- No frontend changes.
- The run-mode helpers (`_resolve_run_mode`, `_web_live_run_options`, …) and
  `RUN_MODE_OPTIONS` stay in `digest.web.app`; they are a separate concern.
