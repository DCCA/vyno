# AI Daily Digest Architecture (Current)

## Document Status
- Status: Current architecture baseline
- Updated: 2026-03-14
- Source of truth alignment: `README.md`, `src/digest/*`, `web/src/*`, `compose.yaml`

## System Overview
AI Daily Digest is a Python runtime with a local web API and React operator console. It ingests configured AI content sources, executes a scoring/summarization pipeline, delivers outputs to Telegram and Obsidian, and persists run data in SQLite for observability and control-plane features.

```text
                               +--------------------------------+
                               |     Config + Environment       |
                               | config/sources.yaml            |
                               | config/profile.yaml            |
                               | data/*.local.yaml overlays     |
                               | .env / env vars                |
                               +---------------+----------------+
                                               |
                                               v
+---------------------+             +----------+-----------+              +----------------------+
| React Web Console   | <---------> | FastAPI Web API      | <----------> | SQLite Store         |
| web/src/App.tsx     |  HTTP JSON  | src/digest/web/app.py|   read/write | runs, items, scores, |
| dashboard/schedule/run           | run status/progress   |              | selected-items,      |
| sources/profile/history          | onboarding/config ops |              | feedback, timeline,  |
| timeline review                 | archive + feedback    |              | health/history data  |
+---------------------+             +----------+-----------+              +----------+-----------+
                                               |                                     ^
                                               | invokes                              |
                                               v                                     |
                                     +---------+----------+                          |
                                     | Runtime Orchestrator|--------------------------+
                                     | src/digest/runtime.py
                                     +---------+----------+
                                               |
                 +-----------------------------+-----------------------------+
                 |                             |                             |
                 v                             v                             v
      +----------+-----------+       +---------+----------+       +----------+-----------+
      | Connectors/Ingestion |       | Pipeline + Quality  |       | Delivery               |
      | rss/youtube/x/github |       | normalize/dedupe    |       | telegram + obsidian    |
      | src/digest/connectors|       | score/select/summarize      | src/digest/delivery    |
      +----------------------+       | repair/fallback      |       +------------------------+
                                     | src/digest/pipeline  |
                                     | src/digest/scorers   |
                                     | src/digest/summarizers|
                                     +----------------------+

                      +-------------------------+--------------------------+
                      | CLI + Bot + Scheduler + Doctor                     |
                      | src/digest/cli.py                                   |
                      | run / schedule / doctor / bot / web / bot-health    |
                      +-----------------------------------------------------+
```

## Runtime Entry Points
- `digest run`: manual execution, full pipeline.
- `digest schedule`: schedule loop with timezone/time target.
- `digest doctor`: onboarding/preflight verification checks.
- `digest bot`: Telegram admin command loop.
- `digest web`: starts config API consumed by Vite UI.
- `digest bot-health-check`: validates bot heartbeat artifact.

## Component Responsibilities
- `src/digest/connectors/*`
  - External source fetch and source-specific parsing.
- `src/digest/pipeline/*`
  - Canonical item normalization, dedupe, scoring orchestration, selection, summarization prep.
- `src/digest/scorers/agent.py`
  - Agentic scoring/tagging via OpenAI Responses API with retries and controls.
- `src/digest/summarizers/*`
  - LLM summarization path plus extractive fallback path.
- `src/digest/quality/online_repair.py`
  - Must-read quality repair stage with fail-open behavior controls.
- `src/digest/delivery/*`
  - Telegram rendering/sending and Obsidian note writing.
- `src/digest/ops/*`
  - Onboarding, source/profile registries, run lock, Telegram ops commands.
- `src/digest/storage/sqlite_store.py`
  - Persistence for runs, scoring artifacts, diagnostics, and observability feeds.
- `src/digest/web/app.py`
  - API routes for run state, onboarding, config edits, schedule state, timeline/history, source health, and seen reset.
- `web/src/App.tsx`
  - Route-based operator console that coordinates onboarding and post-activation workspaces.

## Primary Data Flows

### Flow: Live Run
1. Runtime loads effective sources/profile from base config + local overlays.
2. Connectors fetch candidates from all configured source groups.
3. Pipeline normalizes and deduplicates items.
4. Scoring combines profile heuristics and optional agent scoring.
5. Ranking applies quality-learning, feedback bias, content-depth, source-preference, and research-balance adjustments.
6. Selection computes `Must-read`, `Skim`, and `Videos`.
7. Summarization executes LLM/extractive paths with guardrails.
8. Delivery sends Telegram digest and writes Obsidian note.
9. Store persists run metadata, selected items, archived artifacts, errors, and observability events.

### Flow: Web Control Plane
1. UI calls `/api/*` endpoints with token header when enabled.
2. API authenticates request based on auth mode and token configuration.
3. API returns redacted config state where secret-like keys are masked.
4. Mutations persist overlays (`data/sources.local.yaml`, `data/profile.local.yaml`) and append history/timeline records.

### Flow: Digest Review and Feedback
1. Timeline reads archived run artifacts and selected items from SQLite and `.runtime/run-artifacts/`.
2. The UI renders the delivered Telegram and Obsidian payloads exactly as archived.
3. Item and source feedback is posted through the web API.
4. Feedback is stored with derived feature rows and later reused as ranking bias in runtime.

### Flow: Web Scheduling
1. The operator saves `profile.schedule` through the dedicated `Schedule` workspace.
2. The web API scheduler loop reads that schedule plus current run-lock state.
3. Quiet-hours rules are evaluated in the configured local timezone before any run is started.
4. Due runs start through the same live-run machinery used by the UI.
5. Scheduler status is persisted to `.runtime/schedule-state.json` and exposed through `/api/schedule/status`.

### Flow: Onboarding
1. Preflight checks validate env, config, and runtime prerequisites.
2. Source packs bootstrap starter source sets.
3. Preview run executes safe validation path.
4. Activate triggers live run and updates onboarding milestones.

## State and Storage Model
- Base tracked config:
  - `config/sources.yaml`
  - `config/profile.yaml`
- Local mutable overlays:
  - `data/sources.local.yaml`
  - `data/profile.local.yaml`
- Runtime and output artifacts:
  - `digest-live.db`
  - `logs/digest.log`
  - `.runtime/config-history/*`
  - `.runtime/run-artifacts/<run_id>/*`
  - `.runtime/schedule-state.json`
  - `.runtime/*` (locks, bot heartbeat)
  - `obsidian-vault/` notes

## API Security and Access Model
- Auth mode env var: `DIGEST_WEB_API_AUTH_MODE=required|optional|off`.
- Token env var: `DIGEST_WEB_API_TOKEN`.
- Token header configurable via `DIGEST_WEB_API_TOKEN_HEADER`.
- CORS defaults allow localhost and private-lan development origins.
- Secret-like fields are redacted in API responses and rehydrated on save when unchanged.

## Reliability and Observability
- Run lock prevents overlapping conflicting runs.
- Structured JSON logging includes run/stage metadata.
- Source health aggregation highlights failing sources from the latest completed run and suggested fixes.
- Timeline stores per-run event stream, severity, summary, operator notes, selected items, and exact delivered artifacts for non-preview runs.
- Config history snapshots support rollback from the web console.
- Scheduler state tracks next run, last result, active run, and scheduler errors.
- Bot runtime heartbeat supports Docker healthcheck validation.
- Selected-item records preserve raw score, adjusted score, and adjustment breakdown for operator review.

## Deployment Topologies
- Local developer mode:
  - `make app` starts API (`127.0.0.1:8787`) + UI (`127.0.0.1:5173`).
- Service split mode:
  - `make web-api` and `make web-ui` in separate shells.
- CLI automation mode:
  - `make schedule` runs the standalone CLI scheduler loop.
- Background scheduler service mode:
  - `make docker-scheduler-up` runs a detached Docker service that hosts `digest web` for always-on scheduling.
  - `make docker-scheduler-deploy` rebuilds and recreates that service after local code changes.
- Bot runtime mode:
  - `digest bot` directly or Docker Compose managed service.
- Default Docker operator stack mode:
  - `make docker-up` starts both `digest-bot` and `digest-scheduler`.
  - Docker exports `OBSIDIAN_VAULT_PATH=/app/obsidian-vault` so Obsidian delivery lands in the mounted host vault.

## Architectural Requirements

### Requirement: Config Overlay Safety
The architecture SHALL preserve tracked baseline config and isolate mutable runtime edits in overlay files.

#### Scenario: Runtime source edit
- GIVEN an operator adds a source in UI or bot command
- WHEN mutation is persisted
- THEN tracked `config/sources.yaml` remains unchanged
- AND delta is written to `data/sources.local.yaml`

### Requirement: Observable Execution
The architecture SHALL persist enough event/run data to diagnose failures without rerunning workloads.

#### Scenario: Source failure diagnosis
- GIVEN a run completes with source errors
- WHEN the operator opens source health, timeline, schedule, or history views
- THEN failing source, last error, and run linkage are available
- AND corrective hints are displayed

### Requirement: Delivered Artifact Persistence
The architecture SHALL preserve exact delivered artifacts for non-preview runs.

#### Scenario: Archived digest retrieval
- GIVEN a completed non-preview run
- WHEN an operator requests archived run artifacts
- THEN the system can return the exact Telegram payload and Obsidian note written for that run
- AND the archive survives container restarts through mounted runtime storage

### Requirement: Ranking Transparency
The architecture SHALL separate raw scoring from post-score ranking adjustments.

#### Scenario: Adjusted score review
- GIVEN a selected run item
- WHEN the operator inspects it in review surfaces
- THEN raw score, adjusted score, and adjustment breakdown are available
- AND the user-facing digest score reflects the adjusted score rather than raw score alone

### Requirement: Dedicated Scheduler State
The architecture SHALL persist scheduler state separately from ordinary run records so the operator can inspect automation posture without waiting for a new run.

#### Scenario: Scheduler inspection
- GIVEN the web scheduler is enabled
- WHEN the operator opens the schedule workspace
- THEN next run timing, current scheduler status, last trigger result, and latest scheduler error are available
- AND those values remain available across page refreshes while the API process is running

### Requirement: Safe Control Plane Access
The architecture SHALL support strict local API protection with explicit token-based authentication.

#### Scenario: Unauthorized request
- GIVEN auth mode is `required`
- WHEN a client omits or sends an invalid API token
- THEN protected API endpoints reject the request
- AND no config mutation is applied
