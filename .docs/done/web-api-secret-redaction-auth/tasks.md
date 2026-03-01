# Tasks: Web API Secret Redaction and Authentication

- [x] 1.0 Implement API auth middleware and env controls
  - [x] 1.1 Add auth mode/token/header env helpers
  - [x] 1.2 Add middleware to enforce token for protected `/api/*` routes
- [x] 2.0 Implement secret redaction and placeholder rehydration
  - [x] 2.1 Add recursive redaction utility
  - [x] 2.2 Redact profile/effective API responses and snapshot payload fields
  - [x] 2.3 Rehydrate redacted placeholders in validate/diff/save endpoints
- [x] 3.0 Update web UI/startup/docs for authenticated local workflow
  - [x] 3.1 Send API token header from web UI when provided
  - [x] 3.2 Ensure `make app` provides session token to API and UI
  - [x] 3.3 Document auth env vars and usage in README
- [x] 4.0 Verification and archive
  - [x] 4.1 Add/update tests for auth and redaction logic
  - [x] 4.2 Run `make test`
  - [x] 4.3 Run `npm --prefix web run build`
  - [x] 4.4 Smoke test `make app`
  - [x] 4.5 Move change to `.docs/done/` with completion summary
