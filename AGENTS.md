# Repository Guidelines

## Project Structure & Module Organization
This repository is currently documentation-first. The root contains project-level guidance in `FIREHOSE.md`.

Use `.docs/` as the primary workspace for planned and active work:
- `.docs/PRD.md`: product goals, constraints, and non-goals.
- `.docs/todo/`: proposed work not started.
- `.docs/doing/<change-name>/`: active change set (`proposal.md`, `spec.md`, `design.md`, `tasks.md`).
- `.docs/done/<change-name>/`: completed changes and outcomes.

Keep each change scoped to one logical unit of work.

## Build, Test, and Development Commands
No language runtime or build system is configured yet. Use lightweight repo checks while authoring docs and structure:
- `rg --files`: list tracked project files quickly.
- `rg "Requirement:" .docs`: verify requirement sections are present.
- `git status`: review pending edits before commit.
- `git diff -- AGENTS.md FIREHOSE.md`: confirm targeted documentation changes.

Add project-specific build/test commands here when application code is introduced.

## Coding Style & Naming Conventions
Prefer concise, explicit Markdown and small, reviewable diffs.
- Use clear headings and short sections.
- Use RFC 2119 terms in specs (`MUST`, `SHALL`, `SHOULD`, `MAY`).
- Write Given/When/Then scenarios under each requirement.
- Name change folders with lowercase kebab-case (example: `.docs/doing/auth-session-timeout/`).

## Testing Guidelines
Treat verification as mandatory, even for docs-driven work.
- Confirm every planned task is checked off or explicitly deferred.
- Ensure implementation notes match final behavior.
- When code exists, add/update relevant automated tests before moving work to `.docs/done/`.

## Commit & Pull Request Guidelines
This repository has no commit history yet; use this baseline:
- Commit messages: imperative, scoped, and specific (example: `docs: add initial change spec for auth timeout`).
- Keep commits focused; avoid mixing unrelated work.
- PRs should include: summary, affected paths, verification steps, risks, and follow-ups.
- Link related issues/tasks and include screenshots only when UI artifacts are introduced.

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
