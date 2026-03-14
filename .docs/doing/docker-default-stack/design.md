# Design

## Approach
- Change `docker-build` to build both Compose services used by the default Docker workflow.
- Change `docker-up` to start both `digest-bot` and `digest-scheduler` with a single `docker compose up -d ...` invocation.
- Leave split helper targets in place so operators can still inspect or restart bot and scheduler services independently.
- Update README Docker guidance to clarify:
  - `docker-up` is the full local stack
  - `docker-logs` remains bot-focused
  - scheduler-specific helper targets remain available
  - state persists because `data/`, `.runtime/`, `obsidian-vault/`, and `digest-live.db` are bind-mounted

## Verification
- Check `make -n docker-build` to confirm both services are built.
- Check `make -n docker-up` to confirm both services are started.
- Review README text for consistency with the Makefile behavior and mounted persistence model.
