# Tasks

- [x] Create `digest.web.schedule` with the eight schedule helper functions and
      their imports.
- [x] Remove the helper definitions from `digest.web.app` and import them from
      `digest.web.schedule`.
- [x] Confirm every in-module call site resolves via the re-imported names.
- [x] `ruff check src tests` is clean.
- [x] Full backend test suite passes (focus: `test_web_schedule`,
      `test_web_security`).

## Result

- `digest/web/app.py` shrank from 2589 to 2440 lines; new
  `digest/web/schedule.py` holds the 182-line helper module.
- Only the five helpers referenced by `app.py` (including the two imported by
  `test_web_schedule`) are re-imported there; the three internal-only helpers
  live solely in `digest.web.schedule`.
