# Spec: X Follow People + Theme Ingestion

## Scope
Extend X ingestion from inbox-only to selector-based ingestion (`x_author`, `x_theme`) with provider abstraction, cursoring, and operator control parity.

### Requirement: X Source Types for People and Themes
The system SHALL support two new source types: `x_author` and `x_theme`.

#### Scenario: Add person selector
- GIVEN an operator adds `x_author` value `@somehandle` (or canonical handle)
- WHEN the source is saved
- THEN the selector is canonicalized and persisted in source overlay
- AND it appears in effective sources

#### Scenario: Add theme selector
- GIVEN an operator adds `x_theme` query `ai agents evaluation`
- WHEN the source is saved
- THEN the selector is normalized and persisted in source overlay
- AND it appears in effective sources

### Requirement: Backward-Compatible X Inbox Support
The system SHALL preserve existing `x_inbox_path` ingestion behavior.

#### Scenario: Inbox-only mode
- GIVEN no `x_author` and no `x_theme` selectors are configured
- WHEN a run executes with `x_inbox_path` configured
- THEN inbox ingestion behaves as it does today
- AND no selector ingestion is required for run success

### Requirement: Provider-Based X Fetching
The system SHALL fetch X selector content via a provider abstraction with explicit configuration.

#### Scenario: Provider unavailable
- GIVEN selector-based X ingestion is enabled
- WHEN provider credentials/network are unavailable
- THEN source errors are recorded per selector
- AND non-X sources continue through the pipeline

### Requirement: Official Endpoint Compatibility
The system SHALL use officially documented X API endpoints and parameters for author/theme ingestion.

#### Scenario: Author ingestion endpoint usage
- GIVEN selector type `x_author`
- WHEN provider mode is `x_api`
- THEN ingestion uses official user-post retrieval endpoints and parameter bounds
- AND request formation remains compatible with current X API contract

#### Scenario: Theme ingestion endpoint usage
- GIVEN selector type `x_theme`
- WHEN provider mode is `x_api`
- THEN ingestion uses official recent-search endpoint and query syntax rules
- AND pagination uses official next-token mechanics

### Requirement: Incremental Selector Cursoring
The system SHALL persist per-selector cursor/checkpoint state to avoid repeated ingestion of old X posts.

#### Scenario: Incremental follow run
- GIVEN selector cursors exist from previous successful run
- WHEN a new run executes
- THEN fetch starts from the last checkpoint where supported
- AND already-seen X posts are minimized by cursor + existing seen-key logic

### Requirement: Time-Window and Tier Awareness
The system SHALL reflect official X API time-window and tier limitations in behavior and operator feedback.

#### Scenario: Historical request outside allowed window
- GIVEN a selector fetch would require data outside recent-search availability
- WHEN provider/tier does not support full archive
- THEN ingestion uses the supported recent window only
- AND source health or run context records that older history is not available in current tier

### Requirement: Canonical Item Compatibility
The system SHALL normalize selector-ingested X posts into existing canonical `Item` schema.

#### Scenario: Theme post with outbound article link
- GIVEN a fetched theme-matching X post containing an outbound URL
- WHEN normalization runs
- THEN item includes canonical post URL and extracted text context
- AND outbound URL remains available to downstream scoring/summarization context

### Requirement: Operator Control Parity
The system SHALL expose `x_author` and `x_theme` in web and Telegram source management flows.

#### Scenario: Web source mutation
- GIVEN operator opens Sources management in web console
- WHEN adding/removing `x_author` or `x_theme`
- THEN API accepts mutation and persists overlay
- AND action is visible in effective source list

#### Scenario: Bot source mutation
- GIVEN authorized admin uses `/source add x_author ...` or `/source add x_theme ...`
- WHEN command executes
- THEN canonical selector is persisted and listed via `/source list`

### Requirement: Source Health and Error Hints
The system SHALL report selector-level X health failures with actionable hints.

#### Scenario: Author selector fails
- GIVEN provider returns auth/rate-limit error for an author selector
- WHEN run completes
- THEN source health records kind `x_author` with selector identity
- AND hint text points to auth/rate-limit remediation

### Requirement: Safety and Rate Controls
The system SHALL provide bounded fetch limits for X selectors to avoid runaway requests.

#### Scenario: High selector volume
- GIVEN many X selectors are configured
- WHEN run executes
- THEN fetching respects configured per-run caps
- AND run remains bounded in latency and request volume
