# Decision Note: Keep vs Remove Docker Runtime

## Decision Question
Should this project keep Docker runtime support for `digest bot`, or remove it and standardize on host-native process management?

## Current Recommendation
Keep Docker as an optional runtime path for now.

## Why
- Docker currently provides a reproducible, restartable bot runtime with existing project assets (`Dockerfile`, `compose.yaml`, make targets, runbook).
- Removing Docker now would reduce options before a verified replacement path exists.
- In this workspace, Docker validation is unavailable, so immediate removal would be a process decision without equivalent operational proof.

## Keep Criteria
Keep Docker if all of the following remain true:
- At least one target environment uses Docker/Compose for long-running bot uptime.
- Docker path remains low-maintenance (docs + assets stay aligned with CLI behavior).
- Required runtime state persistence is preserved (`config`, `data`, `logs`, `.runtime`, DB, vault mount).
- Recovery expectation is restart-based (`restart: unless-stopped`) and relied on operationally.

## Remove Criteria
Remove Docker only when all of the following are complete:
- A non-Docker replacement runtime is documented and implemented (for example, `systemd` service + restart policy).
- Replacement path is validated for:
  - normal startup
  - process crash recovery
  - host reboot recovery
  - persistence continuity
- Operator runbook and make/dev commands are updated to point to the replacement path.
- Docker assets are explicitly deprecated in docs before deletion (one release/change cycle recommended).

## Decision Gate Checklist
- `G1` Runtime parity: bot command path uses overlays/secrets consistently across local and deployment modes.
- `G2` Health signal quality: operator can distinguish "process alive" from "bot operational".
- `G3` Recovery evidence: crash/reboot behavior validated on a Docker-enabled host.
- `G4` Alternative readiness: non-Docker path exists and passes the same recovery checks.

## Immediate Next Step
Proceed with Docker hardening and parity fixes first; revisit remove/keep only after `G1-G3` are satisfied.
