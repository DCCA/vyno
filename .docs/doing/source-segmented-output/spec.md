# Spec: Source-Segmented Output

### Requirement: Configurable Render Mode
The system SHALL support `output.render_mode` with values `sectioned` and `source_segmented`.

#### Scenario: Invalid mode rejected
- GIVEN `output.render_mode: invalid`
- WHEN profile config loads
- THEN validation fails with a clear error

### Requirement: Source Bucket Rendering
The system SHALL render selected digest items grouped by source family in source-segmented mode.

#### Scenario: Mixed item set
- GIVEN selected items from GitHub, RSS/articles, YouTube, and X
- WHEN render mode is `source_segmented`
- THEN output includes separate source section headers for non-empty buckets

### Requirement: Backward Compatibility
The system SHALL preserve existing `sectioned` rendering behavior by default.

#### Scenario: Default profile
- GIVEN no explicit `render_mode`
- WHEN digest renders
- THEN output follows existing sectioned structure
