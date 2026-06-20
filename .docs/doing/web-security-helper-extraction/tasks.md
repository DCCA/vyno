# Tasks

- [x] Create `digest.web.security` with the seven config constants and nine
      CORS/auth/redaction helper functions.
- [x] Remove the moved constants and functions from `digest.web.app` and import
      the eight route-facing names back; drop now-unused `os`/`re`/`hmac`
      imports.
- [x] Update `test_web_security` and `test_web_cors` to import the security
      symbols from `digest.web.security`.
- [x] Confirm no circular import (`import digest.web.app` succeeds).
- [x] `ruff check src tests` is clean.
- [x] Full backend test suite passes (focus: `test_web_security`,
      `test_web_cors`, `test_web_live_run_options`).

## Result

- `digest/web/app.py` shrank from 1875 to 1751 lines; new
  `digest/web/security.py` holds the 143-line module.
- Cumulative across the session's four extractions (schedule, run_progress,
  sources, security), `app.py` dropped from 2589 to 1751 lines (-838, -32%).
- `os`, `re`, and `hmac` are no longer imported in `app.py` — all of their uses
  lived in the moved security cluster.
