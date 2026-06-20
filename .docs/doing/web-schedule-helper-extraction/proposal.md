# Web Schedule Helper Extraction Proposal

## Why

`src/digest/web/app.py` is the largest backend module (~2.6k lines). The
schedule slot, quiet-hours, and status helpers are pure functions with no route
or `create_app` closure dependencies, so they can move into a focused module
without changing API behavior. This continues the helper-extraction pattern
already applied for `digest.web.feedback`.

## Scope

- Move the schedule helper functions into a new `digest.web.schedule` module:
  `_schedule_config_from_profile`, `_schedule_due_slot_utc`,
  `_local_hhmm_minutes`, `_is_quiet_hours_active`,
  `_advance_schedule_slot_local`, `_next_allowed_schedule_slot_utc`,
  `_schedule_completion_detail`, and `_schedule_status_payload`.
- Re-import the helper names in `digest.web.app` so existing call sites and
  `from digest.web.app import ...` (used by tests) keep working.
- Verify web schedule/security tests and the full backend/security checks.

## Non-goals

- No schedule behavior changes.
- No API shape changes.
- No route or scheduler-loop changes.
- No frontend changes.
