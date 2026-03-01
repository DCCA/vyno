# Completion Summary: hardcode-hygiene-guardrails

## Delivered
- Centralized core constants in `src/digest/constants.py` and migrated dependent modules.
- Strengthened app startup/config plumbing for API auth token/header and host separation.
- Improved UI API request base handling and Vite proxy env loading.
- Added local and CI security guardrails (`detect-secrets`, Bandit high-severity, Ruff runtime/syntax, Semgrep advisory).

## Verification
- `make test` passed.
- `npm --prefix web run build` passed.
- `timeout 25s make app` passed startup smoke (terminated by timeout as expected).
- `make security-check` passed.

## Follow-ups
- Consider tightening Bandit threshold from high-only to medium once current network-call findings are triaged.
- Consider moving Semgrep from advisory to blocking after a false-positive baseline is established.
