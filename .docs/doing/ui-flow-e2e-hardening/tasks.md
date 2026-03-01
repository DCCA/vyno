# Tasks: ui-flow-e2e-hardening

- [ ] 1.0 Fix body parsing reliability for UI POST endpoints
  - [ ] 1.1 Replace model-bound body params with explicit dict payload parsing
  - [ ] 1.2 Keep field validation and error messages explicit

- [ ] 2.0 Add regression tests for web POST flows
  - [ ] 2.1 Add TestClient coverage for source add/remove
  - [ ] 2.2 Add TestClient coverage for source-pack apply and profile save flow

- [ ] 3.0 Run real browser flow verification
  - [ ] 3.1 Execute onboarding/source/review/history actions via browser automation
  - [ ] 3.2 Capture and document observed outcomes

- [ ] 4.0 Verify and archive
  - [ ] 4.1 Run full test suite
  - [ ] 4.2 Run web build
  - [ ] 4.3 Move change to `.docs/done/` with completion summary
