# Design: Dockerize Bot Runtime

## Deployment Shape
Use Docker Compose as the initial deployment target with a bot-first service:
- `digest-bot`: runs `digest bot` continuously.

Optional follow-on services:
- `digest-scheduler`: runs `digest schedule` for autonomous timed runs.
- One-shot `digest-run` command for manual invocation in CI/ops scripts.

## Image Strategy
- Single project `Dockerfile` based on Python 3.11 slim.
- Install project and runtime dependencies (`feedparser`, `beautifulsoup4`, etc.).
- Keep image minimal and deterministic.
- Entrypoint uses existing CLI (`digest`).

## Runtime Mounts
Mount these paths from host to container:
- `config/` (read-only where possible)
- `data/` (for `sources.local.yaml`, X inbox)
- `logs/`
- `.runtime/`
- DB path location (for `digest.db`)

This preserves mutable state across restarts while keeping image immutable.

## Reliability Controls
- Compose `restart: unless-stopped` for bot service.
- Keep existing run-lock semantics (`.runtime/run.lock`) to prevent overlapping manual runs.
- Add heartbeat-based bot health state (`.runtime/bot-health.json`) updated by `digest bot`.
- Add container `healthcheck` via `digest bot-health-check` to fail stale/error-streak states.

## Secrets & Env
- Inject via `.env` and/or host env vars.
- Required for bot mode: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_IDS`, `TELEGRAM_ADMIN_USER_IDS`.
- Recommended: `GITHUB_TOKEN`, `OPENAI_API_KEY`.

## Observability
- Keep JSON log output in mounted `logs/digest.log`.
- Document commands for triage:
  - `docker compose ps`
  - `docker compose logs -f digest-bot`
  - `docker compose restart digest-bot`

## Rollout Plan
1. Add Docker assets (`Dockerfile`, `.dockerignore`, `compose.yaml`).
2. Run smoke tests with mounted volumes and bot command.
3. Validate restart behavior (process kill + host reboot simulation).
4. Document operator runbook and fallback procedures.

## Risks
- Long-poll failures can loop noisily if credentials are invalid.
- SQLite on network mounts can be unreliable; prefer local disk volumes.
- Misconfigured volumes can silently reset state.

## Mitigations
- Fail fast for missing required bot env vars.
- Keep runtime paths explicit and documented.
- Add a post-deploy checklist for first start validation.
