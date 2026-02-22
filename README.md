# 📰 AI Daily Digest

AI Daily Digest ingests high-signal AI content, ranks and tags it, sends a Telegram digest, and archives Markdown notes to Obsidian.

---

## Table of Contents

- [Features](#-features)
- [Repository Structure](#-repository-structure)
- [Quick Start](#-quick-start)
- [Common Commands](#-common-commands)
- [Configuration](#%EF%B8%8F-configuration)
- [Output Format](#-output-format)
- [Logging and Debugging](#-logging-and-debugging)
- [Security Notes](#-security-notes)
- [Known Limitations](#-known-limitations)

---

## ✨ Features

- **Source ingestion:**
  - RSS feeds
  - YouTube channels
  - X links from a manual inbox file
<<<<<<< HEAD
  - GitHub repos/topics/search queries/orgs
- Deduplication, scoring, and selection (`Must-read`, `Skim`, `Videos`)
- Agent-based scoring and tagging via OpenAI Responses API with rules fallback
- Optional LLM summarization via OpenAI Responses API with extractive fallback
- Delivery to Telegram and Obsidian
- Structured JSON logs with run-level traceability
=======
  - GitHub repos/topics/search queries
- **Deduplication, scoring, and selection** (`Must-read`, `Skim`, `Videos`)
- **Agent-based scoring and tagging** via OpenAI Responses API with rules fallback
- **Optional LLM summarization** via OpenAI Responses API with extractive fallback
- **Delivery** to Telegram and Obsidian
- **Structured JSON logs** with run-level traceability
>>>>>>> 33e48d7a8b2b22a8b254968e64dda3c62501a131

---

## 📁 Repository Structure

| Path | Description |
|------|-------------|
| `src/digest/` | Application code |
| `config/` | Runtime configuration (`sources.yaml`, `profile.yaml`) |
| `data/` | Local runtime data templates (for example `x_inbox.example.txt`) |
| `tests/` | Unit and integration tests |
| `.docs/` | Firehose planning/spec history |

---

## 🚀 Quick Start

**1. Copy env template and fill values:**

```bash
cp .env.example .env
```

**2. Install dependencies:**

<details>
<summary>Preferred (<code>uv</code>)</summary>

```bash
uv sync
```

</details>

<details>
<summary>Fallback (<code>venv</code> + <code>pip</code>)</summary>

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

</details>

**3. Review/edit:**

- `config/sources.yaml`
- `config/profile.yaml`
- `data/x_inbox.txt` (copy from template if needed)

**4. Run once:**

```bash
make live
```

---

## 🛠 Common Commands

| Command | Description |
|---------|-------------|
| `make test` | Run tests |
| `make live` | Run once (live) |
| `make schedule` | Run scheduler |
| `make schedule TIME=08:30 TZ=America/New_York` | Scheduler with overrides |
| `make logs` | Tail logs |

---

## ⚙️ Configuration

### `config/sources.yaml`

- `rss_feeds`, `youtube_channels`, `youtube_queries`
- `x_inbox_path`
- `github_repos`, `github_topics`, `github_search_queries`, `github_orgs`
  - `github_orgs` accepts either `org-login` or `https://github.com/org-login`
  - Org ingestion includes repo updates + releases (not issues/PRs)

### `config/profile.yaml`

- **Scoring:**
  - `agent_scoring_enabled: true`
  - `openai_model: gpt-5.1-codex-mini`
<<<<<<< HEAD
- GitHub org guardrails:
  - `github_min_stars`
  - `github_include_forks`
  - `github_include_archived`
  - `github_max_repos_per_org`
  - `github_max_items_per_org`
- Summarization:
=======
- **Summarization:**
>>>>>>> 33e48d7a8b2b22a8b254968e64dda3c62501a131
  - `llm_enabled: false|true`
- **Output:**
  - Telegram token/chat id
  - Obsidian vault/folder
  - `obsidian_naming: timestamped|daily`

### Environment Variables

See `.env.example` for full list.

Most used:

| Variable | Notes |
|----------|-------|
| `OPENAI_API_KEY` | |
| `GITHUB_TOKEN` | Recommended for GitHub API rate limits |
| `TELEGRAM_BOT_TOKEN` | |
| `TELEGRAM_CHAT_ID` | |

---

## 📤 Output Format

- **Telegram:** compact digest sections (`Must-read`, `Skim`, `Videos`)
- **Obsidian:**
  - Default: `AI Digest/YYYY-MM-DD/HHmmss-<run_id>.md`
  - Legacy mode: `AI Digest/YYYY-MM-DD.md`

---

## 🔍 Logging and Debugging

- Default log path: `logs/digest.log`
- Log format: JSON lines with `run_id`, `stage`, `level`, and context fields
- Useful overrides:

| Variable | Purpose |
|----------|---------|
| `DIGEST_LOG_PATH` | Custom log file path |
| `DIGEST_LOG_LEVEL` | Log verbosity level |
| `DIGEST_LOG_MAX_BYTES` | Max log file size |
| `DIGEST_LOG_BACKUP_COUNT` | Number of log backups |

---

## 🔒 Security Notes

- Never commit real secrets to git.
- Use `.env` locally (ignored by `.gitignore`).
- Keep inbox/runtime files private; use tracked templates (`.env.example`, `data/x_inbox.example.txt`) for sharing.

---

## ⚠️ Known Limitations

- In restricted network environments, source fetches may fail and runs can be `partial` or `failed`.
- X ingestion is manual-link based in MVP (no direct X API automation yet).
