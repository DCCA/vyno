# AI Daily Digest

AI Daily Digest is a local-first Python application and web console for turning noisy AI-source inputs into a curated daily brief. It ingests configured sources, scores and selects the highest-signal items, delivers a digest to Telegram, and archives Markdown notes to Obsidian.

## What The Project Does
- Ingests content from RSS feeds, YouTube channels and queries, X inbox links, optional X selectors, and GitHub selectors.
- Normalizes, deduplicates, scores, and selects items into `Must-read`, `Skim`, and `Videos`.
- Uses OpenAI Responses API for agent scoring/tagging and optional summarization, with deterministic fallback behavior.
- Writes run history, source health, seen-state, timeline events, and other observability data to SQLite.
- Exposes a local FastAPI control plane consumed by a Vite/React operator console.

## Current Operator Surfaces
The web console is route-based and currently includes:
- `Dashboard`: overall posture, active run state, alerts, and quick actions
- `Schedule`: dedicated automation cadence, quiet-hours, and scheduler status
- `Run Center`: manual run actions and live progress
- `Sources`: source inventory, local mutations, and source health
- `Profile`: scoring, output, run-policy, and maintenance controls
- `Timeline`: per-run event stream, summary, export, and notes
- `History`: config snapshot ledger and rollback actions
- `Onboarding`: first-run setup flow, preflight, source packs, preview, and activation

When onboarding is incomplete, the primary nav stays focused on setup surfaces. After activation, the app switches to the broader operator workflow.

## Repository Structure
- `src/digest/`: backend runtime, connectors, delivery, scoring, summarization, storage, ops, and web API
- `web/`: Vite + React + Tailwind operator console
- `tests/`: backend unit and integration tests
- `web/tests/`: frontend source-shape tests
- `config/`: tracked base config (`sources.yaml`, `profile.yaml`)
- `data/`: mutable local overlays and runtime templates
- `.docs/`: Firehose product, architecture, backlog, and completion history

## Quick Start
1. Create local env config:

```bash
cp .env.example .env
```

2. Install dependencies:

Preferred:

```bash
uv sync
```

Fallback:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

3. Review the tracked base config and local overlays:
- `config/sources.yaml`
- `config/profile.yaml`
- `data/x_inbox.txt` if you want manual X inbox ingestion
- optional overlays:
  - `data/sources.local.yaml`
  - `data/profile.local.yaml`

4. Start the local app:

```bash
make app
```

5. Run one digest manually:

```bash
make live
```

6. Run preflight checks before activating delivery or schedule flows:

```bash
make doctor
```

## Common Commands
- `make app`: start API and UI together using `scripts/start-app.sh`
- `make web-api`: run the FastAPI control plane only
- `make web-ui`: run the Vite UI only
- `make web-ui-build`: build the UI bundle
- `make live`: execute one live digest run
- `make schedule`: run the CLI scheduler loop
- `make bot`: run the Telegram admin bot loop
- `make doctor`: run onboarding and environment preflight checks
- `make test`: run backend tests
- `npm --prefix web run test`: run frontend tests
- `make security-check`: run baseline security checks
- `make security-check-extended`: run extended security checks

## Local App Startup
`make app` is the friendly default for local work.

It currently:
- starts the API on `http://127.0.0.1:8787`
- starts the UI on `http://127.0.0.1:5173`
- installs missing web dependencies automatically if needed
- fails early when the chosen API or UI port is already in use
- generates a session API token automatically when `DIGEST_WEB_API_AUTH_MODE=required` and no token is already set
- writes startup logs to `.runtime/app-api.log` and `.runtime/app-ui.log`

Stop both processes with `Ctrl+C`.

When running API and UI separately, keep the token and token-header settings aligned in both shells:

```bash
DIGEST_WEB_API_TOKEN=dev-local-token make web-api
VITE_WEB_API_TOKEN=dev-local-token make web-ui
```

## Configuration Model
Tracked base config:
- `config/sources.yaml`
- `config/profile.yaml`

Mutable local overlays:
- `data/sources.local.yaml`
- `data/profile.local.yaml`

Runtime state and artifacts:
- `digest-live.db`
- `logs/digest.log`
- `.runtime/`
- `obsidian-vault/`

The application preserves tracked defaults and writes operator changes into the local overlay files.

## Source Configuration
`config/sources.yaml` supports these source groups:
- `rss_feeds`
- `youtube_channels`
- `youtube_queries`
- `x_inbox_path`
- `x_authors`
- `x_themes`
- `github_repos`
- `github_topics`
- `github_search_queries`
- `github_orgs`

Notes:
- `x_authors` accepts handles such as `openai` or `@openai`, plus profile URLs such as `https://x.com/openai`.
- `x_themes` accepts free-text recent-search queries.
- X selector ingestion is optional and controlled by `DIGEST_X_PROVIDER`. The default `inbox_only` mode uses only the manual inbox file. `x_api` enables author/theme selector fetching through the X recent-search API.
- `github_orgs` accepts either an owner login or a GitHub owner URL. Owner ingestion includes repo updates and releases.

## Profile Configuration
`config/profile.yaml` currently includes:
- topical preferences and blocklists
- GitHub quality guardrails
- LLM scoring and summarization controls
- Must-read diversity controls
- online Must-read quality repair controls
- cross-run quality learning controls
- `run_policy`
- `schedule`
- Telegram and Obsidian output settings

Notable fields:
- `run_policy.default_mode`: `fresh_only`, `balanced`, `replay_recent`, or `backfill`
- `run_policy.allow_run_override`
- `run_policy.seen_reset_guard`: `confirm` or `disabled`
- `schedule.enabled`
- `schedule.cadence`: `daily` or `hourly`
- `schedule.time_local`
- `schedule.hourly_minute`
- `schedule.quiet_hours_enabled`
- `schedule.quiet_start_local`
- `schedule.quiet_end_local`
- `schedule.timezone`
- `output.obsidian_naming`: `timestamped` or `daily`
- `output.render_mode`: `sectioned` or `source_segmented`

## Web API And Security
The FastAPI control plane lives under `/api/*`.

Current security behavior:
- auth modes: `required`, `optional`, `off`
- token env var: `DIGEST_WEB_API_TOKEN`
- token header env var: `DIGEST_WEB_API_TOKEN_HEADER`
- `/api/health` stays reachable for local diagnostics
- config responses redact secret-like fields and preserve unchanged redacted values on save
- default CORS allows localhost and private-network development origins

## Onboarding Flow
The current setup path is:
1. Start `make app`.
2. Open the onboarding workspace.
3. Run preflight and fix any failing checks.
4. Apply a source pack or configure sources manually.
5. Run a preview digest.
6. Activate the product and confirm status.
7. Manage recurring automation from the dedicated `Schedule` workspace.

Preview runs are safe by design: they skip Telegram delivery and production artifact writes.

## Scheduling And Run Control
There are two scheduling paths:
- CLI scheduler: `make schedule`
- Web-app scheduler: save `profile.schedule` through the dedicated `Schedule` workspace

The web scheduler:
- runs inside the web API process
- stores its scheduler state in `.runtime/schedule-state.json`
- reports scheduler status, next run, last trigger, and latest error in the `Schedule` workspace
- supports both daily and hourly cadence
- can suppress runs during quiet hours in local time
- uses incremental defaults for web-triggered scheduled runs
- respects the run lock when another run is already active

Manual runs from the UI live in `Run Center`, where operators can run immediately and follow live progress.

Current recommended hourly setup for Brazil:
- `cadence: hourly`
- `hourly_minute: 0`
- `timezone: America/Sao_Paulo`
- `quiet_hours_enabled: true`
- `quiet_start_local: "22:00"`
- `quiet_end_local: "07:00"`

## Timeline, History, And Source Health
Observability currently includes:
- latest run status and live progress
- source health based on the latest completed run
- timeline runs, events, notes, and JSON export
- config snapshot history and rollback
- structured JSON logs in `logs/digest.log`

This data is stored in SQLite and local history files so operators can inspect failures without rerunning the workload.

## Telegram And Obsidian Output
Telegram:
- chunked digest messages
- sections for `Must-read`, `Skim`, and `Videos`
- admin command bot for status and source operations

Obsidian:
- default naming: `AI Digest/YYYY-MM-DD/HHmmss-<run_id>.md`
- legacy naming: `AI Digest/YYYY-MM-DD.md`
- stable frontmatter fields for downstream retrieval
- `sectioned` or `source_segmented` rendering

## Telegram Admin Commands
When `make bot` is running, authorized admins can use:
- `/status`
- `/digest run`
- `/source wizard`
- `/source list [type]`
- `/source add <type> <value>`
- `/source remove <type> <value>`

Supported runtime source types:
- `rss`
- `youtube_channel`
- `youtube_query`
- `github_repo`
- `github_topic`
- `github_query`
- `github_org`

Runtime-added sources persist into `data/sources.local.yaml`.

## Docker Bot Runtime
Use Docker Compose when you want bot mode to stay up across shell exits or restarts.

Prepare runtime files:

```bash
cp .env.example .env
mkdir -p logs .runtime obsidian-vault
touch digest-live.db
```

Required bot env vars:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ADMIN_CHAT_IDS`
- `TELEGRAM_ADMIN_USER_IDS`

Start the container:

```bash
make docker-build
make docker-up
```

Inspect runtime state:

```bash
make docker-ps
make docker-logs
```

The Compose service mounts `config/`, `data/`, `logs/`, `.runtime/`, `obsidian-vault/`, and `digest-live.db`, and uses `digest bot-health-check` for container health.

Background scheduler service:

```bash
make docker-scheduler-build
make docker-scheduler-up
make docker-scheduler-deploy
```

Useful scheduler commands:
- `make docker-scheduler-logs`
- `make docker-scheduler-ps`
- `make docker-scheduler-restart`
- `make docker-scheduler-deploy` rebuilds and redeploys the scheduler in one command
- `make docker-scheduler-down`

## Environment Variables
See `.env.example` for the full list.

Most commonly used:
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `GITHUB_TOKEN`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_ADMIN_CHAT_IDS`
- `TELEGRAM_ADMIN_USER_IDS`
- `DIGEST_X_PROVIDER`
- `X_BEARER_TOKEN`
- `DIGEST_X_MAX_ITEMS_PER_SELECTOR`
- `DIGEST_WEB_API_AUTH_MODE`
- `DIGEST_WEB_API_TOKEN`
- `DIGEST_WEB_API_TOKEN_HEADER`
- `DIGEST_LOG_PATH`
- `DIGEST_LOG_LEVEL`

## Verification Status
Verified against the current working tree on 2026-03-08:
- `make test` passed (`161` backend tests)
- `npm --prefix web run test` passed (`7` frontend tests)
- `npm --prefix web run build` passed

## Known Limitations
- External API/network conditions can still produce `partial` or `failed` runs.
- X selector ingestion requires `DIGEST_X_PROVIDER=x_api` plus valid X API access; inbox-only remains the default.
- Delivery still targets Telegram and Obsidian only.
