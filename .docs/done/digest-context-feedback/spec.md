# Spec: digest-context-feedback

### Requirement: Digest includes contextual funnel feedback
Digest outputs SHALL include a concise context block that explains what happened during candidate filtering.

#### Scenario: Standard run output
- GIVEN a digest run completes
- WHEN Obsidian and Telegram outputs are rendered
- THEN each output SHALL include contextual run feedback
- AND feedback SHALL include fetched and selected counts

### Requirement: Sparse run explanation
When a run yields very few final items, output SHALL include an explicit sparse-run explanation.

#### Scenario: Sparse run
- GIVEN final selected item count is low
- WHEN output is rendered
- THEN context SHALL explain that strict incremental/quality filtering reduced candidate count

### Requirement: Policy unchanged
Context feedback SHALL be informational only and MUST NOT alter ranking/filtering behavior.

#### Scenario: Filtering behavior
- GIVEN current quality filters and issue gate are enabled
- WHEN context feedback is added
- THEN candidate filtering and section selection behavior remains unchanged
