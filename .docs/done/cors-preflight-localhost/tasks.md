# Tasks: CORS Preflight Localhost Fix

- [x] 1.0 Define and implement CORS helper configuration
  - [x] 1.1 Add helper(s) for default explicit origins
  - [x] 1.2 Add helper(s) for localhost/private-network regex matching
  - [x] 1.3 Apply helpers to FastAPI CORS middleware
- [x] 2.0 Add regression tests
  - [x] 2.1 Add origin-regex acceptance/rejection tests
  - [x] 2.2 Add middleware wiring tests
- [x] 3.0 Verify and archive
  - [x] 3.1 Run `make test`
  - [x] 3.2 Reproduce preflight success for alternate localhost port
  - [x] 3.3 Move change to `.docs/done/` with completion summary
