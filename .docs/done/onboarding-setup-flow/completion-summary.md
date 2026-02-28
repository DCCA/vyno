# Completion Summary: onboarding-setup-flow

## What Changed
- Added onboarding domain logic in `src/digest/ops/onboarding.py` for preflight checks, source packs, onboarding status, and step-state persistence.
- Added onboarding API endpoints in `src/digest/web/app.py` for preflight/status/source-pack apply/preview/activate.
- Added preview-safe runtime behavior in `src/digest/runtime.py` and surfaced preview artifacts through `RunReport`.
- Added `digest doctor` CLI command in `src/digest/cli.py` and a guided onboarding experience in `web/src/App.tsx`.
- Added onboarding and preview safety regression coverage in `tests/test_onboarding.py` and `tests/test_runtime_integration.py`.

## Verification
- `make test` passed.
- `make web-ui-build` passed.
- `make doctor` passed (one warning for missing `data/x_inbox.txt`).

## Follow-ups
- If X inbox ingestion is needed in this environment, create `data/x_inbox.txt` or remove `x_inbox_path` from sources config.
