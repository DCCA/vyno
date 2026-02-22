# Spec: X Posts and GitHub Ingestion

### Requirement: X Manual Inbox Ingestion
The system SHALL ingest X links from a configured inbox source.

#### Scenario: Inbox links are imported
- GIVEN a file or message payload containing valid X links
- WHEN ingest runs
- THEN links are converted into canonical digest items

#### Scenario: Invalid links are skipped
- GIVEN malformed or non-X URLs in the inbox
- WHEN ingest runs
- THEN invalid entries are skipped
- AND ingest continues for valid entries

### Requirement: GitHub API Ingestion
The system SHALL ingest GitHub items using official GitHub APIs.

#### Scenario: Releases and repos are fetched
- GIVEN configured repos/topics/queries and a valid GitHub token
- WHEN ingest runs
- THEN release/repo items are fetched and normalized

#### Scenario: API partial failure
- GIVEN one GitHub endpoint fails
- WHEN ingest runs
- THEN available GitHub endpoints still produce items
- AND run status records partial source failure

### Requirement: Canonical Normalization
The system SHALL normalize X and GitHub content into the existing canonical item schema.

#### Scenario: Mixed-source normalization
- GIVEN RSS, YouTube, X, and GitHub items
- WHEN normalization runs
- THEN all items expose required canonical fields

### Requirement: Scoring and Tagging Compatibility
The system SHALL score and tag X/GitHub items with the existing scoring pipeline.

#### Scenario: Agent scoring applies
- GIVEN X/GitHub normalized items
- WHEN scoring runs
- THEN each item receives score and tags with provider metadata

### Requirement: Delivery Compatibility
The system SHALL include X/GitHub items in Telegram and Obsidian outputs.

#### Scenario: Output includes GitHub/X entries
- GIVEN selected GitHub/X items
- WHEN delivery runs
- THEN rendered digest includes those entries with links and tags

### Requirement: Configuration Controls
The system SHALL support source configuration for X inbox and GitHub selectors.

#### Scenario: Config enables GitHub only
- GIVEN X inbox disabled and GitHub configured
- WHEN run executes
- THEN digest includes GitHub sources without requiring X input
