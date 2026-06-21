# Tasks

- [x] Create `digest.web.run_mode` with `RUN_MODE_OPTIONS`,
      `DEFAULT_WEB_RUN_MODE`, and the five run-mode helper functions.
- [x] Remove the moved definitions from `digest.web.app` and re-import the four
      route-facing names.
- [x] Confirm no circular import (`import digest.web.app` succeeds).
- [x] `ruff check src tests` is clean.
- [x] Full backend test suite passes (focus: `test_web_live_run_options`).

## Result

- `digest/web/app.py` shrank from 1751 to 1688 lines; new
  `digest/web/run_mode.py` holds the 78-line module.
- Cumulative across the session's five `app.py` extractions (schedule,
  run_progress, sources, security, run_mode), `app.py` dropped from 2589 to
  1688 lines (-901, -35%).
