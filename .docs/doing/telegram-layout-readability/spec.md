# Spec: Telegram Layout Readability

### Requirement: Per-Item Source Visibility
The system SHALL show a readable source label for each Telegram digest item.

#### Scenario: Rendered Telegram item
- GIVEN a selected item has a source domain or platform
- WHEN the Telegram digest is rendered
- THEN the item SHALL show a normalized source label near the title

### Requirement: Per-Item Score Visibility
The system SHALL show a reader-friendly score for each Telegram digest item.

#### Scenario: Rendered Telegram item
- GIVEN a selected item has a numeric score
- WHEN the Telegram digest is rendered
- THEN the item SHALL show a qualitative tier and numeric score

### Requirement: Section Signal Without Section Split
The system SHALL show each item's section label without breaking the digest into separate Telegram sections.

#### Scenario: Flat top-10 digest
- GIVEN the Telegram digest is rendered as one ranked list
- WHEN an item belongs to Must-read, Skim, or Videos
- THEN the item SHALL show that section label in its metadata line

### Requirement: Chunk Safety
The system SHALL preserve Telegram message chunking safety after the metadata redesign.

#### Scenario: Long digest with metadata
- GIVEN a digest whose rendered items exceed one Telegram message
- WHEN the digest is chunked
- THEN each message chunk SHALL remain within the configured size limit
- AND item blocks SHALL remain readable and intact
