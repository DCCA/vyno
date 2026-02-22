# Proposal: Telegram Ops Commands

## Why
Operators need to trigger digest runs and manage tracked sources directly from Telegram without shell access.

## Scope
- Add authenticated Telegram command worker mode.
- Add commands to run digest manually and manage sources.
- Add local mutable source overlay storage with safe merge into base sources.
- Add basic run-locking to prevent overlapping manual runs.

## Out of Scope
- Full multi-tenant admin system.
- Editing tracked `config/sources.yaml` from chat.
- Webhook-based bot runtime.
