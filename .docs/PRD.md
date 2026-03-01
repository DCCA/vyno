# AI Daily Digest Product Requirements (Current)

## Document Status
- Status: Current shipped-product PRD baseline
- Updated: 2026-03-01
- Source of truth alignment: `README.md`, `src/digest/*`, `web/src/*`

## Product Intent
AI Daily Digest exists to reduce AI information overload by ingesting multi-source signals, ranking them for quality and relevance, and delivering concise daily output to Telegram and Obsidian with full run traceability.

## Primary Users
- Solo operator who wants a reliable daily AI brief with low noise.
- Power user who tunes source/profile configuration and run policy from a web console.
- Admin operator who controls runtime via Telegram bot commands.

## Product Goals
- The product SHALL support end-to-end digest generation from configured sources without manual data stitching.
- The product SHALL provide both automated and manual run triggers.
- The product SHALL preserve operator trust via observable run status, progress, and source-health diagnostics.
- The product SHALL preserve configuration safety with overlays, diff/review workflows, and explicit auth controls for web API access.
- The product SHALL produce outputs optimized for quick consumption (Telegram) and long-term retrieval (Obsidian Markdown).

## Non-Goals
- Full direct X API automation is NOT required in current scope; X ingestion is manual inbox based.
- Multi-tenant SaaS hosting is NOT in scope.
- Replacing Telegram and Obsidian with new delivery channels is NOT currently required.

## Implemented Scope (Current State)
- Ingestion:
  - RSS feeds
  - YouTube channels and query feeds
  - X links from inbox file
  - GitHub repos, topics, search queries, and organizations
- Pipeline:
  - normalization, dedupe, scoring, selection, summarization
  - Must-read diversity constraints and guardrails
  - quality repair and fallback strategies
- Delivery:
  - Telegram digest sections with chunking
  - Obsidian markdown notes (timestamped default, legacy daily optional)
- Operations:
  - CLI run/schedule/doctor/bot/web modes
  - web console with setup/manage surfaces
  - onboarding preflight, source packs, preview, activate
  - run policy controls and seen-reset controls
  - timeline and history observability
- Security and reliability:
  - API token auth modes (`required|optional|off`)
  - secret redaction in API payloads
  - run lock, bot healthcheck, structured logs, Docker runtime option

## Product Requirements

### Requirement: Multi-Source Ingestion
The system SHALL ingest candidate items from configured RSS, YouTube, X inbox, and GitHub source groups in a single run.

#### Scenario: Mixed source run
- GIVEN configured RSS, YouTube, and GitHub sources
- WHEN a digest run starts
- THEN the run includes candidates from each reachable source type
- AND unreachable sources are recorded as source errors without fully aborting healthy source processing

### Requirement: High-Signal Selection
The system SHALL score and select digest content into `Must-read`, `Skim`, and `Videos` sections with quality and novelty controls.

#### Scenario: Selection output
- GIVEN candidate items are fetched and normalized
- WHEN scoring and selection complete
- THEN each selected item appears in the correct section
- AND near-duplicate or low-signal items are deprioritized or excluded according to profile settings

### Requirement: Dual Output Delivery
The system SHALL deliver digest output to Telegram and Obsidian for each successful live run.

#### Scenario: Live run delivery
- GIVEN Telegram and Obsidian output settings are valid
- WHEN a run completes with selected items
- THEN Telegram messages are rendered and sent
- AND an Obsidian markdown note is written with stable frontmatter fields

### Requirement: Manual and Scheduled Execution
The system SHALL support manual run execution and schedule-driven run execution.

#### Scenario: Scheduled execution
- GIVEN scheduler is running with configured time and timezone
- WHEN the configured schedule boundary is reached
- THEN the digest run executes with incremental defaults
- AND run metadata is persisted for audit and observability

### Requirement: Operability via Web Console
The system SHALL provide a web console for configuration, onboarding, and run observability without direct file editing.

#### Scenario: Setup to manage transition
- GIVEN onboarding is incomplete
- WHEN the operator runs preflight, applies sources, previews, and activates
- THEN onboarding status reaches complete
- AND manage surfaces become the primary operator path

### Requirement: Run Observability
The system SHALL provide run status, live progress, source health, timeline events, and history records.

#### Scenario: Active run monitoring
- GIVEN a run is active
- WHEN the operator opens the dashboard or timeline views
- THEN the UI shows current stage, elapsed progress details, and warning/error counters
- AND the latest completed run remains available for post-run diagnostics

### Requirement: Configuration Safety
The system SHALL apply configuration via tracked base files plus local overlays, with validation and diff visibility.

#### Scenario: Profile editing workflow
- GIVEN an operator edits profile JSON in the web console
- WHEN validate/diff/save actions are performed
- THEN only overlay deltas are persisted
- AND redacted secret placeholders are preserved unless explicitly changed

### Requirement: Access Control and Secret Hygiene
The system SHALL enforce configurable API auth behavior and redact secrets in config responses.

#### Scenario: Required auth mode
- GIVEN `DIGEST_WEB_API_AUTH_MODE=required` and token is configured
- WHEN a client calls a protected `/api/*` endpoint without a valid token
- THEN the request is rejected with unauthorized status
- AND health endpoint remains reachable for local diagnostics

## Constraints and Dependencies
- External APIs and network quality directly affect run completeness.
- `OPENAI_API_KEY` gates agent scoring/summarization capabilities.
- `GITHUB_TOKEN` improves GitHub API reliability and rate limits.
- Telegram and Obsidian outputs depend on valid credentials and writable paths.

## Success Signals
- Daily runs complete with low source and summary error counts.
- Must-read section remains diverse and high quality over time.
- Operators can complete onboarding and run management without shell-level config edits.
- Timeline and source-health surfaces reduce mean time to diagnose failed sources.

## Known Gaps and Future Enhancements
- Native X API ingestion remains future scope.
- More advanced personalization and feedback loops can be expanded beyond current profile controls.
- Additional delivery destinations may be considered after core reliability and signal quality targets are stable.
