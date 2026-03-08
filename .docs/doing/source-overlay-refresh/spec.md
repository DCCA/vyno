# Spec

### Requirement: Local Source Overlay Expansion
The system SHALL support adding new local RSS and YouTube channel sources through `data/sources.local.yaml` without modifying tracked base defaults.

#### Scenario: Add new AI RSS feeds
- GIVEN the base source config already defines tracked default RSS feeds
- WHEN the local overlay adds additional RSS feed URLs
- THEN the effective merged source set SHALL include the new URLs
- AND the tracked base config SHALL remain unchanged

#### Scenario: Add new YouTube channels
- GIVEN the runtime expects canonical YouTube channel IDs
- WHEN the local overlay adds new `youtube_channel` entries
- THEN each added value SHALL be a valid channel ID string
- AND the effective merged source set SHALL include those channels

#### Scenario: Avoid duplicates
- GIVEN a source already exists in either the base config or the overlay
- WHEN the overlay refresh is applied
- THEN the effective merged source set SHALL contain only one canonical copy of that source

### Requirement: Verification
The change SHALL be verified against both config loading and public feed reachability.

#### Scenario: Config loads successfully
- GIVEN the updated overlay file
- WHEN the effective sources are loaded
- THEN config loading SHALL succeed
- AND duplicate canonical values SHALL not be introduced

#### Scenario: Public feeds respond
- GIVEN the new RSS and YouTube channel feed endpoints
- WHEN they are checked over HTTP
- THEN they SHOULD return a successful or expected redirecting response
