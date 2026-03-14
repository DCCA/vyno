# Completion Summary

Changed the default Docker startup flow so the local operator stack starts both the Telegram bot and the scheduler/web service together.

## What Changed
- `make docker-build` now builds both bot and scheduler services.
- `make docker-up` now starts `digest-bot` and `digest-scheduler`.
- Updated docs to explain service split, helper commands, and persistence across restarts.

## Verification
- Verified Make target rendering for the expected Compose commands.

## Risks / Follow-Ups
- Helper commands remain service-specific by design.
