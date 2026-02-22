# Design: MVP Digest Pipeline (Telegram + Obsidian)

## Design Goals
- Keep the first implementation simple and auditable.
- Isolate integrations (sources, LLM, delivery) behind small interfaces.
- Favor graceful degradation over all-or-nothing failure.

## Technology Stack (MVP)
- Runtime: Python 3.12
- CLI: Typer
- Scheduling: APScheduler (or cron invoking CLI)
- HTTP + parsing: httpx, feedparser, readability-lxml, BeautifulSoup
- YouTube extraction: yt-dlp metadata + transcript fallback
- Data + migrations: SQLite, SQLAlchemy, Alembic
- Config + validation: YAML + Pydantic
- Templates: Jinja2 for Telegram and Markdown rendering
- Quality tools: ruff, black, mypy, pytest

## Module Boundaries
- `connectors/`: RSS and YouTube fetchers.
- `pipeline/`: normalize, dedupe, cluster, score, summarize, select.
- `delivery/`: Telegram sender and Obsidian note writer.
- `storage/`: repositories for `items`, `runs`, `scores`, `seen`.
- `cli/`: manual run command and scheduler entrypoints.

## Data Contracts
- `sources.yaml`: rss feeds, youtube channels, youtube queries.
- `profile.yaml`: positive topics/entities, exclusions, trust/deny source lists, output settings.
- Canonical item: `{id, url, title, source, author, published_at, type, raw_text, hash}`.

## LLM Integration (OpenAI Responses API)
- Provide a `Summarizer` interface with two implementations:
  - `ExtractiveSummarizer` (default deterministic fallback)
  - `ResponsesAPISummarizer` (LLM mode)
- `ResponsesAPISummarizer` requirements:
  - Must call OpenAI Responses API (not Chat Completions)
  - Must request structured JSON output: `tldr`, `key_points[]`, `why_it_matters`
  - Must enforce timeout, retry/backoff, and bounded token budget
  - Must record model, latency, token usage, and errors in run metadata
- Fallback behavior:
  - On API failure/timeout/schema violation, return extractive summary and annotate fallback reason

## Pipeline Flow
1. Fetch new items in configured time window.
2. Extract text/transcript and normalize.
3. Deduplicate exact matches and cluster near-duplicates.
4. Compute relevance/quality/novelty scores.
5. Select items under section and total caps.
6. Summarize selected items (Responses API preferred when enabled).
7. Render and deliver Telegram + Obsidian outputs.
8. Persist artifacts for audit and troubleshooting.

## Reliability and Operations
- Continue run on per-source failures.
- Mark run status as success/partial/failure with reasons.
- Ensure idempotent behavior using `seen` table and run windows.

## Tradeoffs
- Rules-based scoring first: faster delivery and easier debugging.
- Optional LLM summaries: better quality at the cost of latency and API dependency.
- SQLite first: low operational overhead; upgrade path to Postgres later.
