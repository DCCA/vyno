# Proposal: Dockerize Bot Runtime

## Why
The digest bot currently depends on a local shell session and manual restarts. Containerizing runtime operations will provide repeatable deployment and better uptime for `digest bot`.

## Scope
- Define a Docker-based deployment plan for bot-first operations.
- Specify container runtime requirements for persistence, secrets, restart behavior, and observability.
- Define a phased implementation plan to reach stable 24/7 bot operation.
- Record explicit keep/remove decision criteria for Docker runtime support (`decision.md`).

## Out of Scope
- Migrating storage from SQLite to external databases.
- Building a full production orchestration stack (Kubernetes, Terraform, managed secrets).
- Re-architecting pipeline logic.
