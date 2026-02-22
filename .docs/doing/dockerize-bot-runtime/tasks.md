# Tasks: Dockerize Bot Runtime

- [x] 1.1 Create Firehose artifacts for Dockerization planning.

- [x] 2.1 Add `Dockerfile` for project runtime image.
- [x] 2.2 Add `.dockerignore` to reduce build context.
- [x] 2.3 Add `compose.yaml` with `digest-bot` service and restart policy.

- [x] 3.1 Define volume mounts for `config`, `data`, `logs`, `.runtime`, and DB path.
- [x] 3.2 Wire env loading for bot credentials and optional provider tokens.
- [x] 3.3 Add healthcheck and document expected healthy state.

- [x] 4.1 Add `make` targets for Docker build/up/down/logs.
- [x] 4.2 Add bot operations runbook section in `README.md`.
- [x] 4.3 Add first-run checklist (env validation, source overlay, log verification).

- [ ] 5.1 Validate containerized `digest bot` start-up with mounted state.
- [ ] 5.2 Validate restart behavior after forced bot process exit.
- [ ] 5.3 Validate persistence across container recreation.

- [x] 6.1 Run test suite and ensure no regression from Docker asset additions.
- [ ] 6.2 Move change to `.docs/done/` after implementation and verification.
