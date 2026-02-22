# Proposal: Admin Panel Ops Console

## Why
Admin operations are currently split across CLI and Telegram commands. A single admin panel reduces operational friction for source management, run control, bot lifecycle checks, logs, output review, and quality feedback.

## Scope
- Add authenticated admin web panel for:
  - Source management (effective + overlay edits)
  - Bot status and lifecycle actions
  - Manual run trigger and run history
  - Log inspection
  - Output inspection
  - Feedback capture and review

## Out of Scope (MVP)
- Multi-tenant RBAC and SSO.
- Rich BI dashboards and advanced analytics.
- Arbitrary filesystem editing.

## Success Conditions
- Admin can complete core operational loop from one UI:
  1. add/remove source
  2. trigger run
  3. inspect logs/output
  4. submit quality feedback
- Existing Telegram and CLI workflows remain functional.
