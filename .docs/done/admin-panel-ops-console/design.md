# Design: Admin Panel Ops Console

## Architecture
- Backend: FastAPI service mounted as internal admin app.
- UI: server-rendered templates (Jinja2) + HTMX for incremental interactions.
- Storage:
  - Existing SQLite runs/scores/items
  - Existing overlay file (`data/sources.local.yaml`)
  - New SQLite tables:
    - `admin_audit`
    - `feedback`

## Security
- Session-based admin auth (single-admin credential for MVP).
- CSRF token validation for all mutating POST actions.
- Secure cookie settings (`HttpOnly`, `SameSite`, expiry).
- Restrict lifecycle commands via explicit allowlist wrappers.

## Process Control Strategy
- Preferred: service manager integration (`systemctl` wrapper script).
- Fallback: lock/pid check with explicit subprocess wrapper.
- Panel never executes arbitrary shell commands.

## Pages
- `/admin/login`
- `/admin/sources`
- `/admin/bot`
- `/admin/runs`
- `/admin/logs`
- `/admin/outputs`
- `/admin/feedback`

## Data Flow
1. Sources page reads effective sources from base + overlay merge.
2. Mutations call existing canonicalization/registry functions.
3. Runs page triggers runtime run with same lock logic.
4. Logs page tails/filters structured JSON logs.
5. Outputs page resolves latest Obsidian notes and Telegram payload chunks.
6. Feedback writes to DB and is visible by run/item.

## Reliability
- Keep Telegram and CLI admin paths as fallback/parallel controls.
- Use pagination and max-row limits for logs and runs.
- Fail-safe behavior: read-only views remain available if control actions fail.

## Rollout
- Phase 1: read-only pages (`runs`, `logs`, `outputs`, `bot status`).
- Phase 2: source management mutations.
- Phase 3: run-now + bot lifecycle controls.
- Phase 4: feedback + audit views.
