# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Daily Digest — a local-first Python + React app that ingests AI news from multiple sources (RSS, YouTube, X/Twitter, GitHub), scores/deduplicates content via OpenAI Responses API, and delivers curated digests to Telegram and Obsidian.

## Common Commands

```bash
# Install dependencies
uv sync                          # preferred (Python)
npm --prefix web install         # frontend

# Run tests
make test                        # 254 backend tests (unittest discover)
npm --prefix web run test        # 24 frontend tests (Node native test runner, across web/tests/*.test.mjs)

# Run a single backend test
uv run python -m unittest tests/test_config.py -v
# Or a specific test method:
uv run python -m unittest tests.test_config.TestConfig.test_method -v

# Start the full app (API + UI)
make app

# Start backend API only (port 8787)
make web-api

# Start frontend dev server only (port 5173)
make web-ui

# Build frontend
make web-ui-build

# Run one digest manually
make live

# Preflight checks
make doctor

# Security scanning
make security-check              # detect-secrets, bandit, ruff, semgrep (local subset)
make security-check-extended     # full scan

# Tail the structured JSON log
make logs

# Interactive first-run wizard (.env + local overlays + deps)
make setup
```

Without `uv`, the Makefile falls back to `PYTHONPATH=src python3` / `PYTHONPATH=src ./bin/digest`.

Ruff is the linter (config in `pyproject.toml`: `target-version = "py311"`, rule set `E4/E7/E9/F`). There is no `.pre-commit-config.yaml`; checks run in CI (`.github/workflows/ci.yml` runs tests on Python 3.11 + 3.12 and the Node suite; `.github/workflows/security.yml` runs the scanners).

### Docker targets

Two service families, each with `build`/`up`/`down`/`logs`/`ps`/`restart`/`deploy`:

- `make docker-*` — the `digest-bot` (Telegram bot) service
- `make docker-scheduler-*` — the `digest-scheduler` (web API + scheduler) service

`deploy` = build + up. To bring up the full stack after tests pass: `make docker-scheduler-deploy && make docker-deploy`.

## Architecture

### Backend (Python 3.11+, `src/digest/`)

Pipeline flow: **Ingest → Normalize → Dedupe → Score → Select → Deliver → Archive**

| Module | Role |
|--------|------|
| `cli.py` | Entry point (`digest = digest.cli:main`) — dispatches `run`, `schedule`, `doctor`, `bot`, `web`, `bot-health-check`. Global args select config/db paths: `--sources`, `--sources-overlay`, `--profile`, `--profile-overlay`, `--db`. `bot-health-check` reads `.runtime/bot-health.json` for Docker liveness probes |
| `runtime.py` | Main orchestrator — runs the full digest pipeline with progress callbacks |
| `models.py` | Core dataclasses (`Item`, `Score`, `ScoredItem`, `DigestSections`, `RunReport`) |
| `config.py` | Config dataclasses loaded from YAML |
| `connectors/` | Source integrations: `rss.py`, `youtube.py`, `x_inbox.py`, `x_selectors.py`, `github.py` |
| `pipeline/` | Processing stages: `normalize.py`, `dedupe.py`, `scoring.py`, `selection.py`, `summarize.py` |
| `scorers/` | OpenAI Responses API agent scoring (`agent.py`) |
| `summarizers/` | `responses_api.py` (LLM) + `extractive.py` (deterministic fallback) |
| `delivery/` | `telegram.py`, `obsidian.py`, `source_buckets.py` |
| `storage/` | `sqlite_store.py` — run history, seen-state, feedback, timeline |
| `quality/` | Online quality learning and repair (`online_repair.py`) |
| `ops/` | Onboarding, profile/source registries, Telegram commands, run locks |
| `web/` | FastAPI control plane (`app.py`) — token-based auth, CORS, all `/api/*` routes |

### Frontend (TypeScript/React, `web/`)

Vite + React Router + Tailwind CSS + Radix UI. Feature-based folder structure under `web/src/features/`: Dashboard, Schedule, RunCenter, Sources, Profile, Timeline, History, Onboarding.

API client in `web/src/lib/api.ts` talks to the FastAPI backend on port 8787.

### Configuration

- **Tracked base**: `config/sources.yaml`, `config/profile.yaml`
- **Local overlays** (mutable, gitignored): `data/sources.local.yaml`, `data/profile.local.yaml`
- **Environment**: `.env` (copy from `.env.example`) — API keys for OpenAI, Telegram, GitHub, X
- **Database**: `digest-live.db` (SQLite)
- **Runtime state**: `.runtime/` (schedule state, bot health, run artifacts)

**Overlay semantics** (`ops/source_registry.py`, `ops/profile_registry.py`): the tracked base YAML is never mutated. UI/bot edits write a **delta-only** overlay to `data/*.local.yaml`; on load the overlay is deep-merged on top of the base (overlay wins); on save only values that differ from the base are persisted. When editing config behavior, change the registry merge logic — do not write back to the tracked base.

### Web control plane auth & secret redaction (`web/security.py`)

- Auth modes via `DIGEST_WEB_API_AUTH_MODE`: `required` (default), `optional`, `off`. In `required` mode every `/api/*` route except `/api/health` and `OPTIONS` needs the token.
- Token in `DIGEST_WEB_API_TOKEN`, sent in header `DIGEST_WEB_API_TOKEN_HEADER` (default `X-Digest-Api-Token`). `scripts/start-app.sh` auto-generates a token when auth is `required` and none is set.
- **Secret redaction**: secret-like fields are returned as `__REDACTED__` in API responses and **rehydrated from the stored value on save** — so a client that PUTs back `__REDACTED__` keeps the existing secret rather than overwriting it. Preserve this round-trip when touching config endpoints.
- CORS defaults allow localhost/dev ports and private LAN ranges; override via `DIGEST_WEB_CORS_ORIGINS` / `DIGEST_WEB_CORS_ORIGIN_REGEX`.

### Docker

Two services in `compose.yaml`: `digest-bot` (Telegram bot) and `digest-scheduler` (web API + scheduler). Build/deploy with `make docker-*` targets.

## FIREHOSE Methodology

This project follows FIREHOSE principles (see `FIREHOSE.md`):

- Use `.docs/` for long-lived specs and context (`.docs/doing/` for active, `.docs/done/` for completed)
- Non-trivial changes start with `proposal.md` + `tasks.md` in `.docs/doing/<change-name>/`
- Prefer small diffs, brownfield-first, one logical unit per change
- Clarify scope before coding; ask when ambiguity affects outcomes
- Keep docs synced with reality; completion summaries go in `.docs/done/`
- Write requirements with RFC 2119 keywords (MUST/SHALL/SHOULD/MAY) plus Given/When/Then scenarios
- When moving a change to `.docs/done/`, keep only `completion-summary.md` and update the folder's `INDEX.md` (prune the rest)

See `.docs/ARCHITECTURE.md` for the current system diagram, primary data flows, and deployment topologies before making structural changes.

## Testing

- Backend: Python `unittest` — tests live in `tests/test_*.py`
- Frontend: Node test runner — tests in `web/tests/*.test.mjs`
- CI runs security scanning (detect-secrets, bandit, semgrep, ruff) on PR/push
