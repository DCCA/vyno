# Completion Summary

Implemented hourly digest scheduling for Brazil time with quiet hours and a background Docker runtime.

## What Changed
- Extended `profile.schedule` to support hourly cadence, quiet-hours controls, and richer scheduler status.
- Updated the web scheduler and Schedule workspace so operators can manage hourly top-of-hour runs in `America/Sao_Paulo`, skipping runs from `22:00` to `07:00`.
- Added a dedicated `digest-scheduler` Docker Compose service plus Make targets so scheduling can continue after the terminal is closed.
- Updated onboarding/profile/dashboard copy and maintained docs to reflect recurring cadence, quiet hours, and the new background service path.

## Effective Runtime Defaults
- `cadence: hourly`
- `hourly_minute: 0`
- `timezone: America/Sao_Paulo`
- `quiet_hours_enabled: true`
- `quiet_start_local: 22:00`
- `quiet_end_local: 07:00`

## Verification
- `make test`
- `npm --prefix web run test`
- `npm --prefix web run build`

## Follow-Ups
- The standalone CLI `schedule` command remains daily-only; the supported background path for this feature is the new Docker scheduler service based on `digest web`.
