# Design: web-live-run-incremental-defaults

## Approach
- Add a small helper in `src/digest/web/app.py` to return live-run options by trigger source.
- Use that helper in `_start_live_run()` so web live runs use incremental settings.
- Keep onboarding preview endpoint unchanged.

## Test strategy
- Add a unit test for helper output to verify web trigger maps to incremental settings.
- Run full test suite and web build.
