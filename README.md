# AI Daily Digest

Daily AI digest pipeline that ingests RSS and YouTube feeds, ranks and summarizes content, sends Telegram output, and archives Markdown notes to Obsidian.

## What It Does
- Ingests from `config/sources.yaml` (RSS feeds, YouTube channels, YouTube queries)
- Normalizes, deduplicates, scores, and selects digest items
- Summarizes with deterministic fallback, or OpenAI Responses API when enabled
- Delivers:
  - Telegram message (if token/chat configured)
  - Obsidian note at `AI Digest/YYYY-MM-DD.md` (if vault path configured)
- Persists audit data in SQLite (`items`, `runs`, `scores`, `seen`)

## Project Layout
- `src/digest/` core application
- `config/` runtime configuration (`sources.yaml`, `profile.yaml`)
- `tests/` unit and integration tests
- `.docs/` Firehose planning/spec artifacts

## Quick Start
1. Create a virtualenv and install dependencies:
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

2. Edit configs:
- `config/sources.yaml`
- `config/profile.yaml`

3. Run once:
```bash
PYTHONPATH=src ./bin/digest --sources config/sources.yaml --profile config/profile.yaml --db digest.db run
```

## Enable OpenAI Responses API Summaries
1. Set in `config/profile.yaml`:
- `llm_enabled: true`
- `openai_model: gpt-4.1-mini`

2. Export API key:
```bash
export OPENAI_API_KEY=your_key_here
```

The implementation uses `POST /v1/responses` with JSON-schema output (`tldr`, `key_points`, `why_it_matters`). If LLM fails, it falls back to extractive summaries.

## Scheduling
Run the built-in scheduler loop:
```bash
PYTHONPATH=src ./bin/digest --sources config/sources.yaml --profile config/profile.yaml --db digest.db schedule --time 07:00 --timezone America/Sao_Paulo
```

For production, prefer cron/systemd invoking the `run` command.

## Testing
Run all tests:
```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Notes
- In offline/sandbox environments, remote source fetches fail and runs can return `failed` or `partial`.
- `.docs/` is project source-of-truth; only ephemeral `.docs/tmp`, `.docs/.cache`, `.docs/drafts` are ignored.
