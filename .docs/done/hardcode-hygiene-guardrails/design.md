# Design: hardcode-hygiene-guardrails

## Constants centralization
- Added `src/digest/constants.py` for shared defaults used by config/runtime/web/connectors.
- Updated modules to import from constants instead of repeating literals.

## Startup/UI configuration hardening
- `scripts/start-app.sh` now separates API bind/public host variables and logs API/UI to `.runtime` files.
- Startup auto-generates a session token when required auth mode has no provided token.
- `web/src/App.tsx` API helper now prefers relative paths when `VITE_API_BASE` is unset.
- `web/vite.config.ts` loads env for proxy target and enforces fixed host/port with strict port behavior.

## Security checks
- Added `.secrets.baseline` and local script `scripts/security-check.sh`.
- `make security-check` runs:
  - detect-secrets baseline guard
  - Bandit high-severity scan (`-lll`)
  - Ruff syntax/runtime safety checks (`E9,F63,F7,F82`)
- `make security-check-extended` adds Semgrep advisory scanning (`p/secrets`, `p/python`).
- Added `.github/workflows/security.yml` to run equivalent checks in CI.
