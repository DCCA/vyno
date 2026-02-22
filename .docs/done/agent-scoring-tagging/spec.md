# Spec: Agent Scoring and Tagging

### Requirement: Agent Scoring
The system SHALL score content with an LLM agent when `agent_scoring_enabled` is true and credentials are available.

#### Scenario: Agent scorer available
- GIVEN valid OpenAI credentials
- WHEN digest scoring executes
- THEN item scores are produced by the agent scorer
- AND score provider is stored as `agent`

### Requirement: Rules Fallback
The system SHALL fallback to rules-based scoring when agent scoring is unavailable or fails.

#### Scenario: Agent call fails
- GIVEN agent scoring fails for an item
- WHEN fallback executes
- THEN rules score is produced for that item
- AND score provider is stored as `rules`

### Requirement: Tagging Output
The system SHALL produce tags per scored item.

#### Scenario: Tags are returned or inferred
- GIVEN any scored item
- WHEN scoring completes
- THEN item has `tags`
- AND item has `topic_tags` and `format_tags` (possibly empty)

### Requirement: Tag Persistence
The system SHALL persist tags and scorer provider with each score row.

#### Scenario: Persisted score metadata
- GIVEN a completed run
- WHEN score rows are queried
- THEN `tags_json`, `topic_tags_json`, `format_tags_json`, and `provider` are present

### Requirement: Tag Delivery to Obsidian
The system SHALL include item tags in Obsidian note content.

#### Scenario: Must-read includes tags
- GIVEN a scored must-read item
- WHEN Obsidian note is rendered
- THEN note includes a tags line for that item
