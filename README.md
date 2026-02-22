# AI Daily Digest

Daily AI digest pipeline that ingests RSS and YouTube feeds, ranks and summarizes content, sends Telegram output, and archives Markdown notes to Obsidian.

## What It Does
- Ingests from `config/sources.yaml` (RSS feeds, YouTube channels, YouTube queries)
- Also supports:
  - X manual inbox links (`x_inbox_path`)
  - GitHub ingestion (`github_repos`, `github_topics`, `github_search_queries`)
- Normalizes, deduplicates, scores, and selects digest items
- Uses agent-based scoring + tagging (with rules fallback)
- Summarizes with deterministic fallback, or OpenAI Responses API when enabled
- Delivers:
  - Telegram message (if token/chat configured)
  - Obsidian note at:
    - `AI Digest/YYYY-MM-DD/HHmmss-<run_id>.md` (`timestamped`, default)
    - `AI Digest/YYYY-MM-DD.md` (`daily`, legacy mode)
- Persists audit data in SQLite (`items`, `runs`, `scores`, `seen`)

## Project Layout
- `src/digest/` core application
- `config/` runtime configuration (`sources.yaml`, `profile.yaml`)
- `tests/` unit and integration tests
- `.docs/` Firehose planning/spec artifacts

## Quick Start
1. Preferred: use `uv`:
```bash
uv sync
```

`make` commands automatically use `uv run ...` when `uv` is installed.

Fallback (if `uv` is not installed):
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

2. Edit configs:
- `config/sources.yaml`
- `config/profile.yaml`

Minimal scoring-related options in `config/profile.yaml`:
```yaml
agent_scoring_enabled: true
openai_model: gpt-5.1-codex-mini
```

Optional GitHub API token for higher limits/private access:
```bash
export GITHUB_TOKEN=your_github_token
```

3. Run once:
```bash
make live
```

## Enable OpenAI Responses API Summaries
1. Set in `config/profile.yaml`:
- `llm_enabled: true`
- `openai_model: gpt-5.1-codex-mini`

2. Export API key:
```bash
export OPENAI_API_KEY=your_key_here
```

Optional model override via env:
```bash
export OPENAI_MODEL=gpt-5.1-codex-mini
```

The implementation uses `POST /v1/responses` with JSON-schema output (`tldr`, `key_points`, `why_it_matters`). If LLM fails, it falls back to extractive summaries.

Scoring/tagging also uses `POST /v1/responses` when `agent_scoring_enabled: true`. On failure, rules scoring is used per item.

## Scheduling
Run the built-in scheduler loop:
```bash
make schedule
```

For production, prefer cron/systemd invoking `make live` (or `uv run digest ... run`).

## Obsidian Naming Modes
Configure in `config/profile.yaml`:
```yaml
output:
  obsidian_naming: "timestamped"  # or "daily"
```

- `timestamped` (default): unique file per run under daily folder.
- `daily`: legacy single file per day (can overwrite on repeated runs).

## Testing
Run all tests:
```bash
make test
```

## Logs
The app writes structured JSON logs to `logs/digest.log` by default.

Tail logs:
```bash
make logs
```

Optional environment overrides:
- `DIGEST_LOG_PATH` (default: `logs/digest.log`)
- `DIGEST_LOG_LEVEL` (default: `INFO`)
- `DIGEST_LOG_MAX_BYTES` (default: `5000000`)
- `DIGEST_LOG_BACKUP_COUNT` (default: `5`)

## Notes
- In offline/sandbox environments, remote source fetches fail and runs can return `failed` or `partial`.
- `.docs/` is project source-of-truth; only ephemeral `.docs/tmp`, `.docs/.cache`, `.docs/drafts` are ignored.
