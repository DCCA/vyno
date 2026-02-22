# Spec: MVP Digest Pipeline (Telegram + Obsidian)

### Requirement: Config-Driven Source Ingestion
The system SHALL ingest content from configured RSS feeds and YouTube channels/queries defined in `sources.yaml`.

#### Scenario: RSS + YouTube items are fetched
- GIVEN valid source entries in `sources.yaml`
- WHEN a digest run starts
- THEN the system fetches new items from RSS and YouTube within the configured time window

#### Scenario: One source class fails
- GIVEN RSS succeeds and YouTube fails for transient reasons
- WHEN the run continues
- THEN the run SHALL complete with available source data and record the partial failure

### Requirement: Profile-Based Topic Filtering and Boosting
The system SHALL apply `profile.yaml` topics/entities/exclusions plus trusted/blocked source rules during scoring.

#### Scenario: Blocked source is excluded
- GIVEN an item from a blocked source
- WHEN scoring is performed
- THEN the item is excluded from selection

### Requirement: Canonical Item Normalization
The system SHALL normalize all fetched inputs into one canonical item schema.

#### Scenario: Mixed source types normalize consistently
- GIVEN article and video inputs
- WHEN normalization runs
- THEN each item has required canonical fields (`id`, `url`, `title`, `source`, `published_at`, `type`, `raw_text`)

### Requirement: Deduplication and Clustering
The system SHALL deduplicate exact duplicates by URL/hash and cluster near-duplicate items.

#### Scenario: Duplicate URLs appear in multiple feeds
- GIVEN two items with the same URL
- WHEN dedupe runs
- THEN one canonical item remains for scoring and selection

### Requirement: Weighted Ranking
The system SHALL compute total score as Relevance (0-60) + Quality (0-30) + Novelty (0-10).

#### Scenario: Score components are auditable
- GIVEN any selected item
- WHEN score inspection is requested
- THEN component scores and total are stored with run context

### Requirement: LLM Summarization via OpenAI Responses API
The system SHALL use OpenAI Responses API for LLM summarization when LLM mode is enabled.

#### Scenario: Responses API returns structured summary
- GIVEN an item selected for digest output
- WHEN LLM summarization is invoked
- THEN the system receives and stores `tldr`, `key_points`, and `why_it_matters`

#### Scenario: Responses API failure fallback
- GIVEN Responses API timeout or error
- WHEN summarization fails
- THEN the system SHALL fall back to deterministic extractive summarization and mark fallback reason in run metadata

### Requirement: Selection Policy and Output Limits
The system SHALL enforce digest composition limits: Must-read 5, Skim 10, Videos 3-5, total <= 20.

#### Scenario: High-volume day still obeys limits
- GIVEN more than 20 high-scoring candidates
- WHEN selection runs
- THEN final output includes no more than 20 items with section limits preserved

### Requirement: Dual Delivery
The system SHALL deliver each digest to Telegram and Obsidian.

#### Scenario: Telegram delivery succeeds
- GIVEN a selected digest payload
- WHEN Telegram send executes
- THEN the daily message format includes Must-read, Skim, Videos, and optional Themes

#### Scenario: Obsidian archive is written
- GIVEN the same selected digest payload
- WHEN Obsidian write executes
- THEN a Markdown file is created at `AI Digest/YYYY-MM-DD.md`

### Requirement: Runtime Modes
The system SHALL support both scheduled daily runs and manual runs via `digest run`.

#### Scenario: Manual trigger executes pipeline
- GIVEN CLI access
- WHEN `digest run` is executed
- THEN a full pipeline run occurs without waiting for scheduler

### Requirement: Persistent Audit Trail
The system SHALL persist runs, items, scores, and seen-history for traceability.

#### Scenario: Run postmortem is possible
- GIVEN a completed run
- WHEN run metadata is queried
- THEN operator can inspect source counts, failures, score outputs, and delivery status
