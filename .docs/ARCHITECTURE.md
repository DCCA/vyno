# AI Daily Digest Architecture (Current)

## Document Status
- Status: Current architecture baseline
- Updated: 2026-03-01
- Source of truth alignment: `README.md`, `src/digest/*`, `web/src/*`, `compose.yaml`

## System Overview
AI Daily Digest is a Python runtime with a local web API and React web console. It ingests configured AI content sources, executes a scoring/summarization pipeline, delivers outputs to Telegram and Obsidian, and persists run data in SQLite for observability and control-plane features.

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
| setup/manage/timeline            | run status/progress   |              | seen, timeline,      |
| profile/sources/review/history   | onboarding/config ops |              | health/history data  |
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
  - API routes for run state, onboarding, config edits, timeline/history, source health.
- `web/src/App.tsx`
  - Single-page operator console with setup and management surfaces.

## Primary Data Flows

### Flow: Live Run
1. Runtime loads effective sources/profile from base config + local overlays.
2. Connectors fetch candidates from all configured source groups.
3. Pipeline normalizes and deduplicates items.
4. Scoring combines profile heuristics and optional agent scoring.
5. Selection computes `Must-read`, `Skim`, and `Videos`.
6. Summarization executes LLM/extractive paths with guardrails.
7. Delivery sends Telegram digest and writes Obsidian note.
8. Store persists run metadata, errors, and observability events.

### Flow: Web Control Plane
1. UI calls `/api/*` endpoints with token header when enabled.
2. API authenticates request based on auth mode and token configuration.
3. API returns redacted config state where secret-like keys are masked.
4. Mutations persist overlays (`data/sources.local.yaml`, `data/profile.local.yaml`) and append history/timeline records.

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
- Source health aggregation highlights repeated failing sources and suggested fixes.
- Timeline stores per-run event stream, severity, summary, and operator notes.
- Bot runtime heartbeat supports Docker healthcheck validation.

## Deployment Topologies
- Local developer mode:
  - `make app` starts API (`127.0.0.1:8787`) + UI (`127.0.0.1:5173`).
- Service split mode:
  - `make web-api` and `make web-ui` in separate shells.
- Bot runtime mode:
  - `digest bot` directly or Docker Compose managed service.

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
- WHEN the operator opens source health and timeline views
- THEN failing source, last error, and run linkage are available
- AND corrective hints are displayed

### Requirement: Safe Control Plane Access
The architecture SHALL support strict local API protection with explicit token-based authentication.

#### Scenario: Unauthorized request
- GIVEN auth mode is `required`
- WHEN a client omits or sends an invalid API token
- THEN protected API endpoints reject the request
- AND no config mutation is applied
