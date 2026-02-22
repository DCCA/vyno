# Spec: Output Format Hardening

### Requirement: Obsidian Structured Notes
The system SHALL generate Obsidian notes with stable frontmatter keys and readable markdown sections.

#### Scenario: Note metadata present
- GIVEN any successful render
- WHEN note content is generated
- THEN frontmatter includes `date`, `generated_at_utc`, `run_id`, `source_count`, and `tags`

### Requirement: Obsidian Readability
The system SHALL format Must-read entries with clear summaries and tags.

#### Scenario: Must-read item formatting
- GIVEN a must-read item with summary and tags
- WHEN note is rendered
- THEN title/link, tags, TL;DR, and why-it-matters fields are present in a consistent layout

### Requirement: Telegram Message Size Safety
The system SHALL split digest output into multiple Telegram messages when content exceeds message limits.

#### Scenario: Oversized digest
- GIVEN a digest text longer than configured limit
- WHEN Telegram payload is rendered
- THEN renderer returns multiple messages each within limit

### Requirement: Telegram Section Clarity
The system SHALL preserve section headers across chunked output.

#### Scenario: Chunked output readability
- GIVEN chunked messages
- WHEN messages are read in order
- THEN sections remain understandable and ordered
