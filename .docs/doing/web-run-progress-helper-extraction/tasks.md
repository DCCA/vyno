# Tasks

- [x] Create `digest.web.run_progress` with `FETCH_STAGES`, `_as_int`, and the
      five run-progress helper functions.
- [x] Remove the moved definitions from `digest.web.app` and import them back
      (keeping `_parse_seen_reset_days` in place).
- [x] Confirm every in-module call site (`FETCH_STAGES`, the five helpers, and
      `_as_int`) resolves via the re-imported names.
- [x] `ruff check src tests` is clean.
- [x] Full backend test suite passes (focus: `test_web_run_progress`,
      `test_web_timeline`).

## Result

- `digest/web/app.py` shrank from 2440 to 2259 lines; new
  `digest/web/run_progress.py` holds the 200-line helper module.
- `FETCH_STAGES` and `_as_int` now live in `digest.web.run_progress` and are
  re-imported into `app.py` (used at the scheduler loop and
  `_parse_seen_reset_days` respectively), avoiding a circular import.
