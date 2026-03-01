# Design: ui-flow-e2e-hardening

## API robustness fix
- Replace local Pydantic model-bound body parameters on web POST routes with explicit `dict[str, Any]` body payload parsing.
- Keep validation semantics by explicit required-field checks and existing domain validation functions.

## Regression testing
- Add API test coverage that exercises POST endpoints through `fastapi.testclient.TestClient` using temporary overlay/db paths.
- Ensure source add/remove and source-pack apply return successful responses for valid payloads.

## Browser verification
- Use `npx agent-browser` for interactive flow checks:
  - onboarding preflight and source-pack apply
  - source add/remove
  - review validate/diff/save
  - history rollback
  - run-now and activate actions
