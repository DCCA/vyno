# Tasks: Digest Configuration Accessibility

- [x] 1.1 Confirm final UX labels for modes and seen policy language.
- [x] 1.2 Confirm default mode decision (`Balanced` vs current incremental strict default).

- [x] 2.1 Add profile schema support for `run_policy` defaults.
- [x] 2.2 Implement runtime resolver mapping mode -> run flags.
- [x] 2.3 Extend `POST /api/run-now` with one-time mode override.
- [x] 2.4 Add `GET/POST /api/config/run-policy` endpoints.

- [x] 3.1 Implement strictness score/level derivation from run context funnel metrics.
- [x] 3.2 Implement top restriction reason attribution.
- [x] 3.3 Add recommendation generator for strict runs.
- [x] 3.4 Expose strictness payload via run summary/timeline APIs.

- [x] 4.1 Add seen reset preview endpoint.
- [x] 4.2 Add seen reset apply endpoint with confirmation contract.
- [x] 4.3 Add audit logging for policy updates and seen resets.

- [x] 5.1 Add Web UI `Digest Policy` panel for default mode.
- [x] 5.2 Add run-once mode override in `Run now` flow.
- [x] 5.3 Add strictness + funnel + reasons section in review/timeline.
- [x] 5.4 Add seen maintenance UI with dry-run preview and confirmation.

- [x] 6.1 Add/Update backend unit tests.
- [x] 6.2 Add/Update API tests.
- [ ] 6.3 Add/Update frontend tests for policy and transparency UI. (deferred: no frontend test harness in repo)
- [x] 6.4 Run regression suite (`make test`, `npm --prefix web run build`).

- [ ] 7.1 Move change to `.docs/done/` with completion summary after implementation and sign-off.
