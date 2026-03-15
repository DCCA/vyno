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
make test                        # 201 backend tests (unittest discover)
npm --prefix web run test        # frontend tests

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
make security-check
```

Without `uv`, the Makefile falls back to `PYTHONPATH=src python3` / `PYTHONPATH=src ./bin/digest`.

## Architecture

### Backend (Python 3.11+, `src/digest/`)

Pipeline flow: **Ingest → Normalize → Dedupe → Score → Select → Deliver → Archive**

| Module | Role |
|--------|------|
| `cli.py` | Entry point — dispatches `run`, `schedule`, `doctor`, `bot`, `web`, `bot-health-check` |
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

### Docker

Two services in `compose.yaml`: `digest-bot` (Telegram bot) and `digest-scheduler` (web API + scheduler). Build/deploy with `make docker-*` targets.

## FIREHOSE Methodology

This project follows FIREHOSE principles (see `FIREHOSE.md`):

- Use `.docs/` for long-lived specs and context (`.docs/doing/` for active, `.docs/done/` for completed)
- Non-trivial changes start with `proposal.md` + `tasks.md` in `.docs/doing/<change-name>/`
- Prefer small diffs, brownfield-first, one logical unit per change
- Clarify scope before coding; ask when ambiguity affects outcomes
- Keep docs synced with reality; completion summaries go in `.docs/done/`

## Testing

- Backend: Python `unittest` — tests live in `tests/test_*.py`
- Frontend: Node test runner — tests in `web/tests/*.test.mjs`
- CI runs security scanning (detect-secrets, bandit, semgrep, ruff) on PR/push
