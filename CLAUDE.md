# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Daily Digest — a local-first Python app that ingests AI news from multiple sources (RSS, YouTube, X/Twitter, GitHub), scores/deduplicates content via OpenAI (LangChain structured output), and delivers curated digests to Telegram and Obsidian.

## Common Commands

```bash
# Install dependencies
uv sync                          # preferred (Python)

# Run tests
make test                        # backend tests (unittest discover)

# Run a single backend test
uv run python -m unittest tests/test_config.py -v
# Or a specific test method:
uv run python -m unittest tests.test_config.TestConfig.test_method -v

# Run one digest manually
make live

# Run the Telegram bot in the foreground
make bot

# Start the scheduler loop (driven by profile.schedule; edit via /schedule in Telegram)
make schedule

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

Ruff is the linter (config in `pyproject.toml`: `target-version = "py311"`, rule set `E4/E7/E9/F`). There is no `.pre-commit-config.yaml`; checks run in CI (`.github/workflows/ci.yml` runs tests on Python 3.11 + 3.12; `.github/workflows/security.yml` runs the scanners).

### Docker targets

Two compose services in `compose.yaml`: `digest-bot` (Telegram bot) and `digest-scheduler` (schedule loop, no ports/healthcheck).

- `make docker-build`/`docker-up`/`docker-deploy` — operate on **both** services (`deploy` = build + up); `make docker-deploy` alone brings up the full stack
- `make docker-logs`/`docker-restart` — `digest-bot` only
- `make docker-scheduler-*` — the same `build`/`up`/`down`/`logs`/`ps`/`restart`/`deploy` family scoped to `digest-scheduler` only

## Architecture

### Backend (Python 3.11+, `src/digest/`)

Pipeline flow: **Ingest → Normalize → Dedupe → Score → Select → Deliver → Archive**

| Module | Role |
|--------|------|
| `cli.py` | Entry point (`digest = digest.cli:main`) — dispatches `run`, `schedule`, `doctor`, `bot`, `bot-health-check`. Global args select config/db paths: `--sources`, `--sources-overlay`, `--profile`, `--profile-overlay`, `--db`. `bot-health-check` reads `.runtime/bot-health.json` for Docker liveness probes |
| `runtime.py` | Main orchestrator — runs the full digest pipeline with progress callbacks |
| `models.py` | Core dataclasses (`Item`, `Score`, `ScoredItem`, `DigestSections`, `RunReport`) |
| `config.py` | Config dataclasses loaded from YAML |
| `connectors/` | Source integrations: `rss.py`, `youtube.py`, `x_inbox.py`, `x_provider.py`, `x_selectors.py`, `github.py` |
| `pipeline/` | Processing stages: `normalize.py`, `clean_text.py`, `dedupe.py`, `scoring.py`, `selection.py`, `summarize.py`, `github_issue_impact.py` |
| `llm/` | Shared LangChain structured-output client (`client.py`) — lazy-imports `langchain-openai`; a missing key/package raises `RuntimeError` so callers fall back to deterministic paths |
| `scorers/` | LLM agent scoring (`agent.py`, via `llm/client.py`) |
| `summarizers/` | `responses_api.py` (LLM, via `llm/client.py`) + `extractive.py` (deterministic fallback) |
| `delivery/` | `telegram.py`, `obsidian.py` |
| `storage/` | `sqlite_store.py` — run history, seen-state, feedback, timeline |
| `quality/` | Online quality learning and repair (`online_repair.py`) |
| `ops/` | Onboarding, profile/source registries, Telegram commands, run locks, paste-a-link source detection (`ingest_detect.py`) |

### Configuration

- **Tracked base**: `config/sources.yaml`, `config/profile.yaml`
- **Local overlays** (mutable, gitignored): `data/sources.local.yaml`, `data/profile.local.yaml`
- **Environment**: `.env` (copy from `.env.example`) — API keys for OpenAI, Telegram, GitHub, X
- **Database**: `digest-live.db` (SQLite)
- **Runtime state**: `.runtime/` (bot health, run artifacts)

**Overlay semantics** (`ops/source_registry.py`, `ops/profile_registry.py`): the tracked base YAML is never mutated. Bot edits write a **delta-only** overlay to `data/*.local.yaml`; on load the overlay is deep-merged on top of the base (overlay wins); on save only values that differ from the base are persisted. When editing config behavior, change the registry merge logic — do not write back to the tracked base.

## FIREHOSE Methodology

This project follows FIREHOSE principles (see `FIREHOSE.md`):

- Use `.docs/` for long-lived specs and context (`.docs/todo/` for planned, `.docs/doing/` for active, `.docs/done/` for completed); `.docs/PRD.md` holds the product requirements
- Non-trivial changes start with `proposal.md` + `tasks.md` in `.docs/doing/<change-name>/`
- Prefer small diffs, brownfield-first, one logical unit per change
- Clarify scope before coding; ask when ambiguity affects outcomes
- Keep docs synced with reality; completion summaries go in `.docs/done/`
- Write requirements with RFC 2119 keywords (MUST/SHALL/SHOULD/MAY) plus Given/When/Then scenarios
- When moving a change to `.docs/done/`, keep only `completion-summary.md` and update the folder's `INDEX.md` (prune the rest)

See `.docs/ARCHITECTURE.md` for the current system diagram, primary data flows, and deployment topologies before making structural changes.

`AGENTS.md` mirrors this guidance for other agents; on process conflicts, `FIREHOSE.md` wins.

## Testing

- Backend: Python `unittest` — tests live in `tests/test_*.py`
- CI runs security scanning (detect-secrets, bandit, semgrep, ruff) on PR/push

## Contribution & merge workflow

Standing pattern for changes made in this repo — always follow it end to end, don't stop at "pushed":

1. **Branch** — develop on a feature branch; never commit directly to `master`.
2. **Commit** — small, focused, scoped commits (imperative subject, e.g. `ops: add ingest suggestion logging`).
3. **Open a PR** against `master` as soon as the change is complete (fill summary / affected paths / verification / risks).
4. **Review** — read the full diff yourself and confirm every CI check run passes: Backend tests (Python 3.11 + 3.12) and the security scan.
5. **Merge** — merge once CI is green. **Never merge with failing or still-pending checks**; wait for them. The repo uses merge commits (see `git log` history), so default to the `merge` method unless asked otherwise.

Deviate only when the user explicitly asks for something different (e.g. leave as draft, hold for their review).
