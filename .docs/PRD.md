# AI Daily Digest Product Requirements (Current)

## Document Status
- Status: Current shipped-product PRD baseline
- Updated: 2026-03-14
- Source of truth alignment: `README.md`, `src/digest/*`, `web/src/*`

## Product Intent
AI Daily Digest exists to reduce AI information overload by ingesting multi-source signals, ranking them for quality and relevance, and delivering concise daily output to Telegram and Obsidian with full run traceability.

## Primary Users
- Solo operator who wants a reliable daily AI brief with low noise.
- Power user who tunes source/profile configuration, run policy, and scheduling from a web console.
- Admin operator who controls runtime via Telegram bot commands.

## Product Goals
- The product SHALL support end-to-end digest generation from configured sources without manual data stitching.
- The product SHALL provide both automated and manual run triggers.
- The product SHALL preserve operator trust via observable run status, progress, and source-health diagnostics.
- The product SHALL preserve configuration safety with overlays, diff/review workflows, and explicit auth controls for web API access.
- The product SHALL produce outputs optimized for quick consumption (Telegram) and long-term retrieval (Obsidian Markdown).
- The product SHALL preserve exact delivered run artifacts and feedback signals so future ranking can learn from what was actually sent.

## Non-Goals
- Full direct X API automation is NOT required in current scope; inbox-only remains the default and selector ingestion is optional.
- Multi-tenant SaaS hosting is NOT in scope.
- Replacing Telegram and Obsidian with new delivery channels is NOT currently required.

## Implemented Scope (Current State)
- Ingestion:
  - RSS feeds
  - YouTube channels and query feeds
  - X links from inbox file
  - optional X author/theme selectors through the recent-search API path
  - GitHub repos, topics, search queries, and organizations
- Pipeline:
  - normalization, dedupe, scoring, selection, summarization
  - Must-read diversity constraints, digest-wide source balancing, and research concentration guardrails
  - quality repair, quality learning, and fallback strategies
  - adjusted scoring with soft source-preference priors, content-depth adjustments, and feedback bias
- Delivery:
  - Telegram digest cards with source, section, and adjusted-score metadata
  - Obsidian markdown notes (timestamped default, legacy daily optional)
  - exact delivered Telegram and Obsidian artifact archiving for non-preview runs
- Operations:
  - CLI run/schedule/doctor/bot/web modes
  - route-based web console with dashboard, schedule, run center, sources, profile, timeline, history, and onboarding surfaces
  - onboarding preflight, source packs, preview, activate, and lifecycle-based navigation
  - run policy controls, seen-reset controls, and dedicated schedule controls for daily or hourly automation
  - timeline digest review, item/source feedback, config history, rollback, and source-health observability
- Security and reliability:
  - API token auth modes (`required|optional|off`)
  - secret redaction in API payloads
  - run lock, scheduler state tracking, quiet-hours suppression, bot healthcheck, and Docker runtime options for bot and scheduler services
  - Docker-safe Obsidian vault override for mounted persistence
  - X per-run spend cap for selector-based discovery

## Product Requirements

### Requirement: Multi-Source Ingestion
The system SHALL ingest candidate items from configured RSS, YouTube, X inbox, optional X selectors, and GitHub source groups in a single run.

#### Scenario: Mixed source run
- GIVEN configured RSS, YouTube, X, and GitHub sources
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

### Requirement: Delivered Run Archive
The system SHALL archive the exact delivered payloads and selected items for each non-preview run.

#### Scenario: Timeline digest review
- GIVEN a non-preview run completed successfully or partially
- WHEN the operator opens Timeline review for that run
- THEN the archived Telegram payload and archived Obsidian note are retrievable
- AND the selected items for that run are available for review

### Requirement: Feedback-Driven Personalization
The system SHALL capture explicit item-level and source-level feedback that can influence future ranking.

#### Scenario: Item review feedback
- GIVEN a prior run is visible in Timeline
- WHEN the operator marks an item as `too_technical` or `more_like_this`
- THEN the feedback is persisted with derived ranking features
- AND subsequent runs may apply that feedback through ranking bias

#### Scenario: Source preference feedback
- GIVEN a source is visible in the Sources surface
- WHEN the operator marks it as preferred, less preferred, or muted
- THEN the feedback is persisted
- AND mute behavior can update blocked-source controls

### Requirement: Cost-Bounded X Discovery
The system SHALL enforce a per-run spend cap for X selector fetching.

#### Scenario: X budget enforcement
- GIVEN X selector discovery is enabled
- WHEN the run computes per-selector fetch limits
- THEN the total X post budget stays within the configured per-run spend cap
- AND zero-budget selectors are skipped cleanly

### Requirement: Final Score Transparency
The system SHALL show the final adjusted ranking score in user-facing digest surfaces.

#### Scenario: Telegram score display
- GIVEN an item is selected into a delivered digest
- WHEN Telegram is rendered
- THEN the displayed score reflects the final adjusted score used for ranking
- AND raw scoring remains available only for operator inspection surfaces

### Requirement: Manual and Scheduled Execution
The system SHALL support manual run execution and schedule-driven run execution from both CLI and web-app workflows.

#### Scenario: Scheduled execution
- GIVEN the web app is running and `profile.schedule` is enabled with a configured time and timezone
- WHEN the configured schedule boundary is reached
- THEN the scheduler triggers a digest using web/schedule run defaults
- AND run metadata and scheduler state are persisted for audit and observability

### Requirement: Operability via Web Console
The system SHALL provide a web console for configuration, onboarding, and run observability without direct file editing.

#### Scenario: Setup to manage transition
- GIVEN onboarding is incomplete
- WHEN the operator runs preflight, applies sources, previews, and activates
- THEN onboarding status reaches complete
- AND the main operator navigation expands to the full route-based workspace set

### Requirement: Run Observability
The system SHALL provide run status, live progress, source health, timeline events, timeline notes, and config history records.

#### Scenario: Active run monitoring
- GIVEN a run is active
- WHEN the operator opens the dashboard, schedule, or timeline views
- THEN the UI shows current stage, elapsed progress details, and warning/error counters
- AND the latest completed run remains available for post-run diagnostics

### Requirement: Dedicated Schedule Controls
The system SHALL provide a dedicated schedule workspace for recurring automation controls and scheduler diagnostics.

#### Scenario: Schedule workspace management
- GIVEN the operator opens the schedule workspace
- WHEN they save, pause, resume, or inspect automation
- THEN they can manage `profile.schedule` without editing raw profile JSON
- AND the page shows next run timing, scheduler state, and the latest scheduler issue near the controls

#### Scenario: Hourly quiet-hours automation
- GIVEN the operator selects hourly cadence with quiet hours in `America/Sao_Paulo`
- WHEN the local time falls between `22:00` and `07:00`
- THEN no digest run starts during that window
- AND the next scheduled run points to the next allowed morning hour

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
- X selector ingestion depends on `DIGEST_X_PROVIDER=x_api` plus valid X API access.
- Telegram and Obsidian outputs depend on valid credentials and writable paths.

## Success Signals
- Daily runs complete with low source and summary error counts.
- Must-read section remains diverse and high quality over time.
- Operators can complete onboarding and run management without shell-level config edits.
- Timeline and source-health surfaces reduce mean time to diagnose failed sources.
- Feedback and digest review improve personalization without making scores misleading or source-biased.

## Known Gaps and Future Enhancements
- Richer native X workflows beyond inbox-only default plus current selector support remain future scope.
- Feedback is currently local-first and operator-driven; richer automatic personalization remains future scope.
- Historical runs from before artifact archiving do not have exact backfilled Telegram payloads.
- Additional delivery destinations may be considered after core reliability and signal quality targets are stable.
