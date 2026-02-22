# Spec: YouTube Noise Sanitization

### Requirement: YouTube Noise Cleaning
The system SHALL remove low-signal promotional blocks and link dumps from YouTube content text.

#### Scenario: Promo-heavy description
- GIVEN a video item with sponsor lines, Patreon lines, hashtags, and many links
- WHEN normalization runs
- THEN cleaned text retains technical substance and excludes low-signal promo/link dump blocks

### Requirement: Summary Quality Guardrail
The system SHALL reject low-signal summaries and use fallback summarization.

#### Scenario: Summary contains URL dump
- GIVEN a generated summary with excessive URLs and spam patterns
- WHEN summary validation runs
- THEN summary is replaced by fallback summarization output

### Requirement: Renderer Safety Caps
The system SHALL cap rendered field lengths for output channels.

#### Scenario: Oversized summary text
- GIVEN very long title and summary fields
- WHEN Telegram and Obsidian renderers format output
- THEN rendered lines remain bounded and readable
