# AI Daily Digest

AI Daily Digest ingests high-signal AI content, ranks and tags it, sends a Telegram digest, and archives Markdown notes to Obsidian.

## Features
- Source ingestion:
  - RSS feeds
  - YouTube channels
  - X links from a manual inbox file
  - GitHub repos/topics/search queries/orgs
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
- Run Telegram command bot:
  - `PYTHONPATH=src ./bin/digest --sources config/sources.yaml --profile config/profile.yaml --db digest-live.db bot`
- Docker operations:
  - Build image: `make docker-build`
  - Start bot service: `make docker-up`
  - View bot logs: `make docker-logs`
  - Service status: `make docker-ps`
  - Restart bot: `make docker-restart`
  - Stop services: `make docker-down`

## Docker Bot Runbook
Use Docker Compose when you want `digest bot` to stay up after shell exits and host restarts.

1. Prepare runtime files:
```bash
cp .env.example .env
mkdir -p logs .runtime obsidian-vault
touch digest-live.db
```

2. Set required bot env vars in `.env`:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ADMIN_CHAT_IDS`
- `TELEGRAM_ADMIN_USER_IDS`

3. If writing Obsidian notes in-container, set:
- `OBSIDIAN_VAULT_PATH=/app/obsidian-vault`
- `OBSIDIAN_FOLDER=AI Digest`

4. Build and start:
```bash
make docker-build
make docker-up
```

5. Validate health and logs:
```bash
make docker-ps
make docker-logs
```

Expected state:
- `digest-bot` is `Up`.
- Logs do not repeatedly show auth/env errors.
- Telegram `/status` command responds from an authorized admin account.

### Persistence Model
Container runtime state is persisted on host mounts:
- `config/` (read-only in container)
- `data/` (includes `sources.local.yaml` and inbox file)
- `logs/`
- `.runtime/` (run lock, runtime artifacts)
- `digest-live.db`
- `obsidian-vault/`

### Healthcheck
`compose.yaml` defines a healthcheck for the bot container process command line.
Use `docker compose ps` to inspect health status.

## Configuration
### `config/sources.yaml`
- `rss_feeds`, `youtube_channels`, `youtube_queries`
- `x_inbox_path`
- `github_repos`, `github_topics`, `github_search_queries`, `github_orgs`
  - `github_orgs` accepts either `org-login` or `https://github.com/org-login`
  - Org ingestion includes repo updates + releases (not issues/PRs)

### `config/profile.yaml`
- Scoring:
  - `agent_scoring_enabled: true`
  - `max_agent_items_per_run` (default `40`)
  - `min_llm_coverage` (default `0.9`)
  - `max_fallback_share` (default `0.1`)
  - `agent_scoring_retry_attempts` (default `1`)
  - `agent_scoring_text_max_chars` (default `8000`)
  - `openai_model: gpt-5.1-codex-mini`
- GitHub quality guardrails:
  - `github_min_stars`
  - `github_include_forks`
  - `github_include_archived`
  - `github_max_repos_per_org`
  - `github_max_items_per_org`
  - `github_repo_max_age_days`
  - `github_activity_max_age_days`
- Summarization:
  - `llm_enabled: false|true`
- Output:
  - Telegram token/chat id
  - Obsidian vault/folder
  - `obsidian_naming: timestamped|daily`
  - `render_mode: sectioned|source_segmented`

### Environment Variables
See `.env.example` for full list.
Most used:
- `OPENAI_API_KEY`
- `GITHUB_TOKEN` (recommended for GitHub API rate limits)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- Bot admin controls:
  - `TELEGRAM_ADMIN_CHAT_IDS` (comma-separated)
  - `TELEGRAM_ADMIN_USER_IDS` (comma-separated)

## Telegram Ops Commands
When bot mode is running, authorized admins can use:
- `/status`
- `/digest run`
- `/source wizard`
- `/source list [type]`
- `/source add <type> <value>`
- `/source remove <type> <value>`

Supported source types:
- `rss`
- `youtube_channel`
- `youtube_query`
- `github_repo`
- `github_topic`
- `github_query`
- `github_org`

Runtime-added sources are persisted in `data/sources.local.yaml` (overlay), merged with tracked `config/sources.yaml`.

## Output Format
- Telegram: compact digest sections (`Must-read`, `Skim`, `Videos`) with automatic chunking for long digests
- Obsidian:
  - Default: `AI Digest/YYYY-MM-DD/HHmmss-<run_id>.md`
  - Legacy mode: `AI Digest/YYYY-MM-DD.md`
  - Stable frontmatter keys (`date`, `generated_at_utc`, `run_id`, `source_count`, `tags`)
  - Must-read rendered as summary callouts for better scanability
- YouTube noise guardrails:
  - promotional/source-link dump cleanup before summarization
  - summary quality fallback on low-signal outputs

## Logging and Debugging
- Default log path: `logs/digest.log`
- Log format: JSON lines with `run_id`, `stage`, `level`, and context fields
- Includes LLM scoring coverage telemetry (`llm_coverage`, `fallback_share`, `fallback_reasons`)
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
