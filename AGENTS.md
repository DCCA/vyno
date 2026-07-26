# Repository Guidelines

## Firehose Precedence
- `FIREHOSE.md` is the project source-of-truth for process and documentation workflow.
- Agents MUST follow `FIREHOSE.md` instructions when planning, implementing, and cleaning docs artifacts.
- If `AGENTS.md` and `FIREHOSE.md` differ, follow `FIREHOSE.md` unless the user explicitly overrides it.
- Docs refactors/cleanup MUST preserve Firehose structure (`.docs/todo`, `.docs/doing`, `.docs/done`) and required artifacts.

## Project Structure & Module Organization
AI Daily Digest is a Python application. The operator surface is the Telegram bot plus the CLI/Makefile - there is no web console.

Key paths:
- `src/digest/`: runtime, connectors, delivery, ops.
- `tests/`: Python unit/integration tests.
- `config/`: tracked base config (`sources.yaml`, `profile.yaml`).
- `data/`: local overlays/templates (`sources.local.yaml`, `profile.local.yaml`, `x_inbox.example.txt`).
- `.docs/`: Firehose planning and history (`PRD.md`, `todo/`, `doing/`, `done/`).

Keep each change scoped to one logical unit of work.

## Build, Test, and Development Commands
Primary commands:
- `make test`: run Python test suite.
- `make schedule`: run the CLI scheduler loop.
- `make bot`: run the Telegram admin bot.
- `make docker-scheduler-up`: run the background Docker scheduler service.
- `make docker-scheduler-deploy`: rebuild and redeploy the background Docker scheduler service in one command.
- `make live`: execute one digest run.
- `make doctor`: run onboarding/preflight checks.
- `make security-check`: run security baseline checks.

Useful checks:
- `rg --files`
- `git status`
- `git diff -- AGENTS.md FIREHOSE.md README.md`

## Coding Style & Naming Conventions
- Keep diffs small, explicit, and reviewable.
- Follow existing project patterns before introducing new abstractions.
- For Firehose docs/specs, use RFC 2119 (`MUST`, `SHALL`, `SHOULD`, `MAY`) and Given/When/Then scenarios.
- Use lowercase kebab-case for change folder names in `.docs/doing/` and `.docs/todo/`.

## Testing Guidelines
Verification is mandatory:
- Run `make test` for backend/runtime changes.
- Keep docs task lists synced with actual completion or explicit deferrals.
- Before moving a change from `.docs/doing/` to `.docs/done/`, ensure completion notes reflect real behavior.

## Commit & Pull Request Guidelines
- Commit messages: imperative, scoped, and specific (example: `ops: detect source type from pasted url`).
- Keep commits focused; avoid mixing unrelated work.
- PRs should include: summary, affected paths, verification steps, risks, and follow-ups.
- Link related issues/tasks.

## Runtime & Config Essentials
- Runtime uses base configs plus overlays:
  - Base: `config/sources.yaml`, `config/profile.yaml`
  - Overlay: `data/sources.local.yaml`, `data/profile.local.yaml`
- Local DB default: `digest-live.db`
- Logs default: `logs/digest.log`
- The schedule model supports hourly cadence and quiet hours in addition to daily mode, configured via `profile.schedule` and the Telegram `/schedule` command.

High-signal source types in current system include:
- `rss`, `youtube_channel`
- `x_author`, `x_theme` (optional X selectors; supports handle and profile URL canonicalization for `x_author`)
- `github_repo`, `github_topic`, `github_query`, `github_org`

## Docs Hygiene
- Keep `.docs/done/` summary-first:
  - one `completion-summary.md` per done change folder
  - `.docs/done/INDEX.md` as central history index
- Keep full historical detail recoverable through git history.
- Use `.docs/todo/` for deferred/not-started work; `.docs/doing/` only for active work.
