# AI Daily Digest

AI Daily Digest ingests high-signal AI content, ranks and tags it, sends a Telegram digest, and archives Markdown notes to Obsidian.

## Features
- Source ingestion:
  - RSS feeds
  - YouTube channels
  - X links from a manual inbox file
  - GitHub repos/topics/search queries
- Deduplication, scoring, and selection (`Must-read`, `Skim`, `Videos`)
- Agent-based scoring and tagging via OpenAI Responses API with rules fallback
- Optional LLM summarization via OpenAI Responses API with extractive fallback
- Delivery to Telegram and Obsidian
- Structured JSON logs with run-level traceability

## Repository Structure
- `src/digest/`: application code
- `config/`: runtime configuration (`sources.yaml`, `profile.yaml`)
- `data/`: local runtime data templates (for example `x_inbox.example.txt`)
- `tests/`: unit and integration tests
- `.docs/`: Firehose planning/spec history

## Quick Start
1. Copy env template and fill values:
```bash
cp .env.example .env
```

2. Install dependencies:
- Preferred (`uv`):
```bash
uv sync
```
- Fallback (`venv` + `pip`):
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

3. Review/edit:
- `config/sources.yaml`
- `config/profile.yaml`
- `data/x_inbox.txt` (copy from template if needed)

4. Run once:
```bash
make live
```

## Common Commands
- Run tests: `make test`
- Run once (live): `make live`
- Run scheduler: `make schedule`
- Scheduler with overrides: `make schedule TIME=08:30 TZ=America/New_York`
- Tail logs: `make logs`

## Configuration
### `config/sources.yaml`
- `rss_feeds`, `youtube_channels`, `youtube_queries`
- `x_inbox_path`
- `github_repos`, `github_topics`, `github_search_queries`

### `config/profile.yaml`
- Scoring:
  - `agent_scoring_enabled: true`
  - `openai_model: gpt-5.1-codex-mini`
- Summarization:
  - `llm_enabled: false|true`
- Output:
  - Telegram token/chat id
  - Obsidian vault/folder
  - `obsidian_naming: timestamped|daily`

### Environment Variables
See `.env.example` for full list.
Most used:
- `OPENAI_API_KEY`
- `GITHUB_TOKEN` (recommended for GitHub API rate limits)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## Output Format
- Telegram: compact digest sections (`Must-read`, `Skim`, `Videos`)
- Obsidian:
  - Default: `AI Digest/YYYY-MM-DD/HHmmss-<run_id>.md`
  - Legacy mode: `AI Digest/YYYY-MM-DD.md`

## Logging and Debugging
- Default log path: `logs/digest.log`
- Log format: JSON lines with `run_id`, `stage`, `level`, and context fields
- Useful overrides:
  - `DIGEST_LOG_PATH`
  - `DIGEST_LOG_LEVEL`
  - `DIGEST_LOG_MAX_BYTES`
  - `DIGEST_LOG_BACKUP_COUNT`

## Security Notes
- Never commit real secrets to git.
- Use `.env` locally (ignored by `.gitignore`).
- Keep inbox/runtime files private; use tracked templates (`.env.example`, `data/x_inbox.example.txt`) for sharing.

## Known Limitations
- In restricted network environments, source fetches may fail and runs can be `partial` or `failed`.
- X ingestion is manual-link based in MVP (no direct X API automation yet).
