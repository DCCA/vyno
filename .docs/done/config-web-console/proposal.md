# Proposal: Config Web Console (shadcn + Tailwind + Vite)

## Why
Config changes through raw YAML and Telegram/CLI flows are functional but slow for frequent tuning. A dedicated web console improves speed, confidence, and rollback safety for operational configuration updates.

## Scope
- Add a web API for config reads/writes, validation, run-now trigger, and snapshot history.
- Build a Vite React UI using shadcn/ui and Tailwind for:
  - source management
  - profile editing
  - validation + diff review
  - snapshot history + rollback
  - run-now action and run status visibility
- Persist profile updates in overlay (`data/profile.local.yaml`) instead of base file edits.

## Out of Scope
- Full bot lifecycle/logs panel parity in this change.
- Multi-user auth and RBAC.
- Hosted deployment concerns.
