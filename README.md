# AI Daily Digest

AI Daily Digest is a local-first Python application for turning noisy AI-source inputs into a curated daily brief. It ingests configured sources, scores and selects the highest-signal items, delivers a digest to Telegram, and archives Markdown notes to Obsidian. There is no web console - the operator surface is the Telegram bot plus the CLI/Makefile.

## Product Thesis

AI Daily Digest is a personal AI signal desk: it helps a user decide what to read, skim, try, or ignore by combining source curation, scoring, delivery, feedback, and archive workflows in one local-first system.

The product bet is that AI information overload is not solved by another feed. It is solved by an operator workflow that preserves source context, ranks signal, supports feedback, and sends the right summary to the right place.

## Project Status

Current as of 2026-06-27:
- backend test suite passes (`make test`)
- latest default-branch CI and Security GitHub Actions workflows pass on `master`

## What The Project Does
- Ingests content from RSS feeds, YouTube channels, X inbox links, optional X selectors, and GitHub selectors.
- Normalizes, deduplicates, scores, and selects items into `Must-read`, `Skim`, and `Videos`.
- Uses OpenAI Responses API for agent scoring/tagging and optional summarization, with deterministic fallback behavior.
- Applies post-score ranking adjustments for diversity, content depth, feedback bias, and soft source preferences.
- Writes run history, seen-state, and other observability data to SQLite.
- Archives delivered Telegram payloads, Obsidian notes, and selected run items for later review and feedback.

## Current Operator Surfaces
There is no web console. The operator surface is:
- **Telegram bot admin commands** (`make bot`, or the `digest-bot` Docker service): status, run control, source management (including auto-detected `/source add <url>`), schedule control, run history, doctor checks, settings, and feedback.
- **CLI / Makefile**: one-off runs (`make live`), the schedule loop (`make schedule`), preflight (`make doctor`), and the setup wizard (`make setup`).

See "Telegram Admin Commands" below for the full command list.

## Repository Structure
- `src/digest/`: runtime, connectors, delivery, scoring, summarization, storage, ops
- `tests/`: backend unit and integration tests
- `config/`: tracked base config (`sources.yaml`, `profile.yaml`)
- `data/`: mutable local overlays and runtime templates
- `.docs/`: Firehose product, architecture, backlog, and completion history

## Quick Start

```bash
git clone <repo-url> && cd vyno
make setup
```

The setup wizard checks your system, installs dependencies, and creates local overlay files, then points you at `make live`, `make bot`, or `make schedule` to actually run the app. The first-run path is designed to work without API keys; add them later for AI-powered scoring, Telegram delivery, GitHub API quota, or optional X selector features.

`make doctor` is a preflight for an already prepared local profile. If you run it before `make setup`, it may report missing local overlays or keys that setup would normally create or keep optional for preview mode.

<details>
<summary>Manual setup (advanced)</summary>

1. `cp .env.example .env` — optionally add your OpenAI key
2. `uv sync`
3. `make live` (one-off run), `make bot` (Telegram bot), or `make schedule` (daily loop)

</details>

## Common Commands
- `make live`: execute one live digest run
- `make schedule`: run the scheduler loop (driven by `profile.schedule`, which the Telegram `/schedule` commands edit; exactly-once per slot with catch-up)
- `make bot`: run the Telegram admin bot loop
- `make doctor`: run onboarding and environment preflight checks
- `make test`: run backend tests
- `make security-check`: run baseline security checks
- `make security-check-extended`: run extended security checks

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
- `x_author` discovery can promote outbound non-X links into first-class digest candidates and preserve X endorsement context when duplicates merge.
- `github_orgs` accepts either an owner login or a GitHub owner URL. Owner ingestion includes repo updates and releases.

## Profile Configuration
`config/profile.yaml` currently includes:
- topical preferences and blocklists
- GitHub quality guardrails
- LLM scoring and summarization controls
- Must-read diversity controls
- online Must-read quality repair controls
- cross-run quality learning controls
- content-depth preference and soft source-preference controls
- X per-run cost and spend controls
- `run_policy`
- `schedule`
- Telegram and Obsidian output settings

Notable fields:
- `run_policy.default_mode`: `fresh_only`, `balanced`, `replay_recent`, or `backfill`
- `run_policy.allow_run_override`
- `run_policy.seen_reset_guard`: `confirm` or `disabled`
- `content_depth_preference`: `practical`, `balanced`, or `deep_technical`
- `trusted_sources`: soft preferred-source prior, not a raw quality boost
- `x_cost_per_post_usd`
- `x_max_spend_per_run_usd`
- `schedule.enabled`
- `schedule.cadence`: `daily` or `hourly`
- `schedule.time_local`
- `schedule.hourly_minute`
- `schedule.quiet_hours_enabled`
- `schedule.quiet_start_local`
- `schedule.quiet_end_local`
- `schedule.timezone`

## Onboarding Flow
The current setup path is:
1. Run `make setup` (or the manual steps above) to install dependencies and create local overlay files.
2. Run `make doctor` to preflight environment, config, and API-key checks - the same checks the Telegram `/doctor` command reports.
3. Configure sources via `data/sources.local.yaml` or the Telegram `/source` command.
4. Run `make live` for a first digest run.
5. Start `make bot` for Telegram admin commands and/or `make schedule` for the daily automation loop.

## Scheduling And Run Control
Scheduling runs through the CLI loop: `make schedule` (or the Telegram `/schedule` command to inspect and change `profile.schedule` at runtime).

The scheduler:
- reads `profile.schedule` (cadence, time, timezone, quiet hours) from the effective profile
- supports both daily and hourly cadence
- can suppress runs during quiet hours in local time
- uses incremental defaults for scheduled runs
- respects the run lock when another run is already active

Manual runs are triggered with `make live` or the Telegram `/digest run [mode]` command.

Current recommended hourly setup for Brazil:
- `cadence: hourly`
- `hourly_minute: 0`
- `timezone: America/Sao_Paulo`
- `quiet_hours_enabled: true`
- `quiet_start_local: "22:00"`
- `quiet_end_local: "07:00"`

## Run History And Diagnostics
Observability is available through:
- `/status`: latest run status, active schedule, and source counts
- `/history [last|run_id]`: recent run history
- `/doctor`: preflight/health checks (env, config, connectivity)
- structured JSON logs in `logs/digest.log`
- run metadata, selected items, and archived delivered artifacts stored in SQLite and `.runtime/run-artifacts/<run_id>/`

This data is stored in SQLite and local history files so operators can inspect failures without rerunning the workload.

## Telegram And Obsidian Output
Telegram:
- chunked digest messages
- flat ranked item cards with source, section, and final adjusted score metadata
- admin command bot for status, source, schedule, history, doctor, settings, and feedback operations

Obsidian:
- naming: `AI Digest/YYYY-MM-DD/HHmmss-<run_id>.md` (always timestamped)
- stable frontmatter fields for downstream retrieval
- sectioned rendering

Delivered archive and feedback:
- non-preview runs archive Telegram chunks under `.runtime/run-artifacts/<run_id>/telegram.json`
- non-preview runs archive the rendered Obsidian note under `.runtime/run-artifacts/<run_id>/obsidian.md`
- the Telegram `/feedback` command records source-level feedback (`mute`/`trust`) and reports an aggregate rating summary (`/feedback summary`)
- delivered digest messages carry per-item thumbs-up/down buttons; a tap records item-level feedback that biases future ranking

## Telegram Admin Commands
When `make bot` (or the `digest-bot` Docker service) is running, authorized admins can use:
- `/status` - run status, schedule, sources
- `/digest run [mode]` - trigger a run (`fresh_only`, `balanced`, `replay_recent`, `backfill`)
- `/schedule` - view/toggle schedule, quiet hours, timezone
- `/history [last|run_id]` - run history
- `/doctor` - system health check
- `/settings` - content depth, run mode, LLM, exclusions
- `/source wizard` - manage sources interactively
- `/source list [type]` - list sources
- `/source add <url-or-handle>` - auto-detects the source type from a pasted GitHub repo/org URL, an X profile URL or `@handle`, a YouTube channel URL/id, or a page (falls back to RSS feed autodiscovery); preflights it and asks for one inline confirm before writing the overlay. If no connector can ingest the link, it is logged as an ingest suggestion for later triage instead of failing outright.
- `/source add <type> <value>` / `/source remove <type> <value>` - explicit add/remove
- `/feedback mute|trust <type> <value>` - block or prefer a source
- `/feedback summary` - aggregate feedback rating counts
- `/help` - list all commands

Supported runtime source types:
- `rss`
- `youtube_channel`
- `x_author`
- `x_theme`
- `github_repo`
- `github_topic`
- `github_query`
- `github_org`

Runtime-added sources persist into `data/sources.local.yaml`.

## Docker Bot Runtime
Use Docker Compose when you want the local operator stack to stay up across shell exits or restarts.

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

Default full-stack startup:

```bash
make docker-build
make docker-up
```

This now starts both `digest-bot` and `digest-scheduler` so Telegram admin commands and the schedule loop are running together for a new local setup.

Inspect runtime state:

```bash
make docker-ps
make docker-logs
```

Helper command behavior:
- `make docker-logs` and `make docker-restart` remain bot-focused helpers.
- `make docker-scheduler-logs`, `make docker-scheduler-ps`, and `make docker-scheduler-restart` remain scheduler-focused helpers.

Persistence across restarts:
- the Compose services mount `config/`, `data/`, `logs/`, `.runtime/`, `obsidian-vault/`, and `digest-live.db`
- source additions, overlay config edits, and run history persist across container restarts because those paths live on the host
- Docker exports `OBSIDIAN_VAULT_PATH=/app/obsidian-vault` so containerized runs write notes into the mounted host vault instead of an internal container path
- code changes still require rebuild/restart because application code is baked into the image

The bot service uses `digest bot-health-check` for container health.

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
- `DIGEST_LOG_PATH`
- `DIGEST_LOG_LEVEL`

## Verification Status
Verified against the current working tree on 2026-06-27:
- `make test` passed (backend tests)
- latest GitHub Actions `CI` run passed on `master`
- latest GitHub Actions `Security` run passed on `master`

## Known Limitations
- External API/network conditions can still produce `partial` or `failed` runs.
- X selector ingestion requires `DIGEST_X_PROVIDER=x_api` plus valid X API access; inbox-only remains the default.
- Archived exact Telegram payloads are available for runs created after the archive feature shipped; older historical runs are not backfilled automatically.
- Delivery still targets Telegram and Obsidian only.
