# Repository Guidelines

## Firehose Precedence
- `FIREHOSE.md` is the project source-of-truth for process and documentation workflow.
- Agents MUST follow `FIREHOSE.md` instructions when planning, implementing, and cleaning docs artifacts.
- If `AGENTS.md` and `FIREHOSE.md` differ, follow `FIREHOSE.md` unless the user explicitly overrides it.
- Docs refactors/cleanup MUST preserve Firehose structure (`.docs/todo`, `.docs/doing`, `.docs/done`) and required artifacts.

## Project Structure & Module Organization
AI Daily Digest is a Python application with a web console.

Key paths:
- `src/digest/`: runtime, connectors, delivery, web API.
- `web/`: Vite + React + Tailwind admin/config console.
- `tests/`: Python unit/integration tests.
- `web/tests/`: frontend source-shape tests.
- `config/`: tracked base config (`sources.yaml`, `profile.yaml`).
- `data/`: local overlays/templates (`sources.local.yaml`, `profile.local.yaml`, `x_inbox.example.txt`).
- `.docs/`: Firehose planning and history (`PRD.md`, `todo/`, `doing/`, `done/`).

Keep each change scoped to one logical unit of work.

## Build, Test, and Development Commands
Primary commands:
- `make test`: run Python test suite.
- `make app`: start API + UI together (`scripts/start-app.sh`).
- `make web-api`: run config API only.
- `make web-ui`: run UI dev server only.
- `make web-ui-build`: build UI.
- `npm --prefix web run test`: run frontend tests.
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
- Run `npm --prefix web run test` and `npm --prefix web run build` for web UI changes.
- Keep docs task lists synced with actual completion or explicit deferrals.
- Before moving a change from `.docs/doing/` to `.docs/done/`, ensure completion notes reflect real behavior.

## Commit & Pull Request Guidelines
- Commit messages: imperative, scoped, and specific (example: `web(ui): localize action feedback by surface`).
- Keep commits focused; avoid mixing unrelated work.
- PRs should include: summary, affected paths, verification steps, risks, and follow-ups.
- Link related issues/tasks and include screenshots only when UI artifacts are introduced.

## Runtime & Config Essentials
- Runtime uses base configs plus overlays:
  - Base: `config/sources.yaml`, `config/profile.yaml`
  - Overlay: `data/sources.local.yaml`, `data/profile.local.yaml`
- Local DB default: `digest-live.db`
- Logs default: `logs/digest.log`
- Web API auth defaults to required mode; when running API/UI separately, keep matching token/header env vars.

High-signal source types in current system include:
- `rss`, `youtube_channel`, `youtube_query`
- `x_author`, `x_theme` (X selectors; supports handle and profile URL canonicalization for `x_author`)
- `github_repo`, `github_topic`, `github_query`, `github_org`

## Docs Hygiene
- Keep `.docs/done/` summary-first:
  - one `completion-summary.md` per done change folder
  - `.docs/done/INDEX.md` as central history index
- Keep full historical detail recoverable through git history.
- Use `.docs/todo/` for deferred/not-started work; `.docs/doing/` only for active work.

## UI Feedback Locality Pattern
Use this as a default UX rule for all web surfaces.

- Feedback MUST be shown close to the action that triggered it (same card/section, near the control row).
- Global top-of-page alerts SHOULD be reserved for global/system events (boot failures, auth/session issues, app-wide outages).
- Success feedback SHOULD auto-dismiss after a short timeout; error feedback SHOULD persist until dismissed or corrected.
- Feedback MUST include non-color cues (explicit title/text) and SHOULD use `aria-live` semantics:
  - polite for success/info
  - assertive for errors/blockers
- Table-row actions (for example edit/delete) SHOULD render feedback near the table region, with row identity in message text.
- Destructive actions SHOULD keep confirmation and result feedback in the same local interaction zone.
