# Web Run-Progress Helper Extraction Proposal

## Why

`src/digest/web/app.py` is still the largest backend module. The run-progress,
stage-labeling, and timeline-severity helpers are pure functions with no route
or `create_app` closure dependencies, so they can move into a focused module
without changing API behavior. This continues the helper-extraction pattern
already applied for `digest.web.feedback` and `digest.web.schedule`.

## Scope

- Move the run-progress helpers into a new `digest.web.run_progress` module:
  the `FETCH_STAGES` set, `_as_int`, `_count_fetch_targets`,
  `_timeline_event_severity`, `_run_stage_label`, `_run_stage_detail`, and
  `_estimate_run_progress_percent`.
- Re-import the moved names in `digest.web.app` so existing call sites and
  `from digest.web.app import ...` (used by `test_web_run_progress`) keep
  working.
- Verify run-progress/timeline tests and the full backend/security checks.

## Non-goals

- No progress-estimation or stage-labeling behavior changes.
- No API shape changes.
- No route or scheduler-loop changes.
- No frontend changes.
- `_parse_seen_reset_days` stays in `digest.web.app` (it parses route payloads,
  not run progress), even though it shares the `_as_int` helper.
