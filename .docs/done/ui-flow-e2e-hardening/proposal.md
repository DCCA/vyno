# Proposal: ui-flow-e2e-hardening

## Why
Web UI flows showed user-facing `TypeError: Failed to fetch` for source mutations despite the API being reachable. This caused broken UX for core setup flows.

## Scope
- Fix API request-body parsing paths that can fail at runtime under FastAPI/Pydantic.
- Add backend regression tests covering POST flows used by the web UI.
- Execute real browser-based flow testing and document outcomes.

## Out of scope
- Redesigning onboarding UX.
- Changing source/profile domain logic.
