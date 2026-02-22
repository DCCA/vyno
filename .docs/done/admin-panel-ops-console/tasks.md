# Tasks: Admin Panel Ops Console

- [x] 1.1 Scaffold admin app module and routing.
- [x] 1.2 Add session auth and CSRF protections.
- [x] 1.3 Add base admin layout and navigation.

- [x] 2.1 Implement read-only Runs page with pagination.
- [x] 2.2 Implement read-only Logs page with filters (`run_id`, `stage`, `level`).
- [x] 2.3 Implement read-only Outputs page (latest Telegram chunks + Obsidian preview).
- [x] 2.4 Implement read-only Bot status page.

- [x] 3.1 Implement Sources page with effective source listing.
- [x] 3.2 Implement add/remove source actions via existing registry APIs.
- [x] 3.3 Implement source mutation audit logging.

- [x] 4.1 Implement Run Now action with existing run lock protections.
- [x] 4.2 Implement bot start/stop/restart controls via restricted wrapper.
- [x] 4.3 Add action confirmations and error surfacing.

- [x] 5.1 Add DB migrations for `feedback` and `admin_audit` tables.
- [x] 5.2 Implement feedback submission and listing by run/item.
- [x] 5.3 Add quality summary view (counts by rating/source).

- [x] 6.1 Add unit tests for auth/session/csrf.
- [x] 6.2 Add unit tests for source mutations and canonicalization integration.
- [x] 6.3 Add tests for run lock behavior from panel actions.
- [x] 6.4 Add tests for log filtering and pagination.
- [x] 6.5 Add tests for feedback CRUD and aggregation.
- [x] 6.6 Add end-to-end smoke test: login -> add source -> run now -> inspect output -> submit feedback.

- [x] 7.1 Update README with admin panel setup and security notes.
- [x] 7.2 Document operational runbook and failure recovery steps.
