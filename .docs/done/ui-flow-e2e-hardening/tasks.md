# Tasks: ui-flow-e2e-hardening

- [x] 1.0 Fix body parsing reliability for UI POST endpoints
  - [x] 1.1 Replace model-bound body params with explicit dict payload parsing
  - [x] 1.2 Keep field validation and error messages explicit

- [x] 2.0 Add regression tests for web POST flows
  - [x] 2.1 Add route-level body parsing coverage for source add/remove
  - [x] 2.2 Add callable endpoint coverage for source-pack apply

- [x] 3.0 Run real browser flow verification
  - [x] 3.1 Execute onboarding/source/review/history actions via browser automation
  - [x] 3.2 Capture and document observed outcomes

- [x] 4.0 Verify and archive
  - [x] 4.1 Run full test suite
  - [x] 4.2 Run web build
  - [x] 4.3 Move change to `.docs/done/` with completion summary
