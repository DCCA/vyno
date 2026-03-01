# Proposal: CORS Preflight Localhost Fix

## Why
The web console can fail with `TypeError: Failed to fetch` when the frontend runs on a localhost port that is not explicitly listed in API CORS allow-origins. In this state, browser preflight requests (`OPTIONS`) return `400` and all API calls fail.

## Scope
- Update web API CORS configuration to accept localhost-style origins on any port used during development.
- Keep CORS constrained to local/private development addresses by default.
- Add regression tests for CORS origin matching and middleware configuration.

## Non-goals
- No production auth or reverse-proxy CORS policy work.
- No changes to endpoint behavior beyond preflight acceptance.
