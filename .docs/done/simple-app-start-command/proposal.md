# Proposal: Simple App Start Command

## Why
Starting the web experience currently requires running separate commands for API and UI. New users can miss one command or start services in the wrong order.

## Scope
- Add one friendly command to start API + UI together.
- Keep existing `make web-api` and `make web-ui` targets unchanged for power users.
- Add documentation for the one-command workflow.

## Non-goals
- No backend API behavior changes.
- No Docker workflow changes.
