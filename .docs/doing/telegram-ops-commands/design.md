# Design: Telegram Ops Commands

## Command Worker
Add `digest bot` CLI command that long-polls Telegram `getUpdates` and routes admin commands.

## Authorization
Require both allowlists:
- `TELEGRAM_ADMIN_CHAT_IDS`
- `TELEGRAM_ADMIN_USER_IDS`

## Source Storage
Use local runtime overlay file `data/sources.local.yaml`:
- `added`: entries to append
- `removed`: tombstones to mask base entries

Effective sources = `config/sources.yaml` + overlay merge (with canonical dedupe).

## Commands
- `/help`
- `/status`
- `/digest run`
- `/source list [type]`
- `/source add <type> <value>`
- `/source remove <type> <value>`

## Safety
- Run lock file prevents overlapping runs.
- Stale lock timeout enables recovery.
- Overlay writes are atomic (`.tmp` + replace).
