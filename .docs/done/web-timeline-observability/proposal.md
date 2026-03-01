# Proposal: Web Timeline Observability

## Why
Admins need a run timeline that works both during execution and after completion so they can diagnose issues and improve source/profile settings with evidence.

## Scope
- Persist structured timeline events for digest runs started from Web.
- Expose Web APIs for timeline runs, events, summaries, and notes.
- Add a Timeline tab in Web admin for live and historical review.
- Allow admins to attach review notes to a run.

## Out of Scope
- Replacing existing JSON file logs.
- Building full dashboards/analytics beyond run-level summaries.
- Implementing SSE/WebSocket streaming (polling-based updates in MVP).

