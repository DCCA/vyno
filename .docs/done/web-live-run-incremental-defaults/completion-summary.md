# Completion Summary: web-live-run-incremental-defaults

## What changed
- Web-triggered live runs now use incremental defaults in `src/digest/web/app.py`:
  - `use_last_completed_window=True`
  - `only_new=True`
  - `allow_seen_fallback=False`
- Added `_web_live_run_options()` helper in `src/digest/web/app.py` to keep option mapping explicit and testable.
- Added test coverage in `tests/test_web_live_run_options.py` for web and non-web option mapping.

## Verification
- `make test` passed.
- `make web-ui-build` passed.

## Notes
- Onboarding preview behavior remains unchanged.
