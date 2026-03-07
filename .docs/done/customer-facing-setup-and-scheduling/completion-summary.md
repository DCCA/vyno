# Completion Summary: customer-facing-setup-and-scheduling

## Outcome
- Added a customer-facing guided setup flow in the onboarding UI, including outputs, starter sources, digest preferences, daily scheduling, preview, first live run, and health confirmation.
- Added first-class daily schedule support to the product model and web API, with schedule persistence in profile overlays and scheduler status/state owned by `digest web`.
- Updated onboarding completion semantics and dashboard messaging so setup is not considered complete until automation is configured and a first live run has completed.

## Affected Areas
- `src/digest/config.py`
- `src/digest/ops/onboarding.py`
- `src/digest/web/app.py`
- `web/src/App.tsx`
- `web/src/features/onboarding/OnboardingPage.tsx`
- `web/src/features/dashboard/DashboardPage.tsx`
- `web/src/features/profile/ProfilePage.tsx`

## Verification
- `python3 -m unittest tests.test_onboarding tests.test_web_payload_binding tests.test_web_schedule -v`
- `npm --prefix web run test`
- `npm --prefix web run build`
- `make test`
- Local browser validation on `http://127.0.0.1:5173/onboarding`
  - setup-first shell and automation status confirmed
  - existing local dev `/api` proxy issue limited deeper interactive validation during `start-app`
