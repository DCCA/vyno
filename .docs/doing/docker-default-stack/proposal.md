# Proposal

## Why
New users reasonably expect the default Docker startup path to bring up the full local operator stack, including the Telegram admin bot. Today the scheduler/web service and the Telegram bot are split across separate make targets, which makes Telegram commands appear broken when only the scheduler is running.

## Scope
- Change the default Docker startup target to launch both `digest-bot` and `digest-scheduler`.
- Align the default Docker build target with that full-stack startup behavior.
- Update docs to explain which services run, which helper commands remain split, and why user changes persist across restarts.

## Non-Goals
- Change Compose service definitions or mounted persistence paths.
- Change Telegram command behavior or auth rules.
- Remove scheduler-specific or bot-specific helper targets.
