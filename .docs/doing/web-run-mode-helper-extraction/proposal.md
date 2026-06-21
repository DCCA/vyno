# Web Run-Mode Helper Extraction Proposal

## Why

`src/digest/web/app.py` still holds the run-mode resolution helpers and their
`RUN_MODE_OPTIONS` table as a top-of-file block. They are pure functions with no
route or `create_app` state, so they can move into a focused module — continuing
the helper-extraction pattern already applied for `feedback`, `schedule`,
`run_progress`, `sources`, and `security`.

## Scope

- Move the run-mode helpers and their config into a new `digest.web.run_mode`
  module: `RUN_MODE_OPTIONS`, `DEFAULT_WEB_RUN_MODE`, `_resolve_run_mode`,
  `_resolve_profile_run_mode`, `_resolve_run_mode_for_request`,
  `_run_mode_options`, and `_web_live_run_options`.
- Re-import the four route-facing names (`RUN_MODE_OPTIONS`,
  `_resolve_profile_run_mode`, `_resolve_run_mode_for_request`,
  `_web_live_run_options`) into `digest.web.app` so existing call sites and
  `from digest.web.app import ...` (used by `test_web_live_run_options`) keep
  working. `DEFAULT_WEB_RUN_MODE`, `_resolve_run_mode`, and `_run_mode_options`
  stay internal to the new module.
- Verify the live-run-options tests and the full backend/security checks.

## Non-goals

- No run-mode resolution behavior changes.
- No API shape changes.
- No route or scheduler-loop changes.
- No frontend changes.
