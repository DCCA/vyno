# Tasks: Dockerize Bot Runtime

- [x] 1.1 Create Firehose artifacts for Dockerization planning.
- [x] 1.2 Add explicit keep/remove Docker decision criteria (`decision.md`).

- [x] 2.1 Add `Dockerfile` for project runtime image.
- [x] 2.2 Add `.dockerignore` to reduce build context.
- [x] 2.3 Add `compose.yaml` with `digest-bot` service and restart policy.

- [x] 3.1 Define volume mounts for `config`, `data`, `logs`, `.runtime`, and DB path.
- [x] 3.2 Wire env loading for bot credentials and optional provider tokens.
- [x] 3.3 Add healthcheck and document expected healthy state.
- [x] 3.4 Align runtime command parity on source/profile overlays for bot-first operations.
- [x] 3.5 Upgrade healthcheck to heartbeat-based bot status (`digest bot-health-check`).

- [x] 4.1 Add `make` targets for Docker build/up/down/logs.
- [x] 4.2 Add bot operations runbook section in `README.md`.
- [x] 4.3 Add first-run checklist (env validation, source overlay, log verification).

- [ ] 5.1 Validate containerized `digest bot` start-up with mounted state. (Deferred: Docker host validation requires docker-group membership or interactive sudo on the target host.)
- [ ] 5.2 Validate restart behavior after forced bot process exit. (Deferred: Docker host validation requires docker-group membership or interactive sudo on the target host.)
- [ ] 5.3 Validate persistence across container recreation. (Deferred: Docker host validation requires docker-group membership or interactive sudo on the target host.)

- [x] 6.1 Run test suite and ensure no regression from Docker asset additions.
- [x] 6.2 Add static regression tests for Docker assets and bot health-check command.
- [x] 6.3 Move change to `.docs/done/` after implementation and verification.
