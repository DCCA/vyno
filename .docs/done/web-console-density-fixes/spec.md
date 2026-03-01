# Spec: Web Console Density Fixes (Sources-Focused)

### Requirement: Feature Parity Preservation
The system SHALL preserve all existing source-management capabilities and API contract behavior.

#### Scenario: Existing source actions remain functional
- GIVEN a user opens the redesigned `Sources` surface
- WHEN they perform add/remove operations
- THEN the UI SHALL execute the same source mutation workflows as before
- AND API payload/endpoint semantics SHALL remain unchanged

#### Scenario: Existing diagnostics remain accessible
- GIVEN source health diagnostics are available
- WHEN the user navigates the redesigned surface
- THEN all diagnostics currently shown SHALL remain accessible
- AND no existing operational control SHALL be removed

### Requirement: Sources Density and Hierarchy Improvement
The system SHALL reduce visual density and improve scanability for source-heavy data.

#### Scenario: Effective sources readability
- GIVEN effective sources include long values and multiple source types
- WHEN the table/list renders
- THEN row density SHALL remain readable without excessive vertical growth
- AND long value fields SHALL be truncated with a clear way to inspect full content

#### Scenario: Source health triage clarity
- GIVEN multiple failing sources exist
- WHEN the source health view renders
- THEN failure-relevant columns SHALL remain visible and scannable
- AND users SHALL be able to triage failures without deep scrolling

### Requirement: Responsive Behavior Across Device Sizes
The system SHALL provide usable layouts for desktop, tablet, and mobile viewports.

#### Scenario: Tablet layout
- GIVEN a tablet viewport
- WHEN the `Sources` surface is opened
- THEN controls and diagnostics SHALL remain usable without overlap or clipping
- AND navigation SHALL not obscure primary actions

#### Scenario: Mobile layout
- GIVEN a mobile viewport
- WHEN source tables are displayed
- THEN source data SHALL remain readable via compact list/card or equivalent adaptive layout
- AND source actions SHALL remain operable without horizontal overflow blocking usage

### Requirement: Loading, Error, and Progress Behavior Preservation
The system SHALL preserve existing async feedback behavior for source and related actions.

#### Scenario: Source mutation loading state
- GIVEN a source add/remove operation is started
- WHEN request is in-flight
- THEN the UI SHALL show loading/disabled state consistent with existing behavior
- AND completion/failure feedback SHALL remain explicit

#### Scenario: Background status polling continuity
- GIVEN periodic status polling is active
- WHEN users navigate across redesigned surfaces
- THEN status/progress updates SHALL continue to function
- AND UI state transitions SHALL remain non-blocking

### Requirement: Accessible Interaction and Motion Safety
The system SHALL provide keyboard-usable controls and reduced-motion safe behavior.

#### Scenario: Keyboard navigation
- GIVEN a keyboard-only user navigates the `Sources` surface
- WHEN focus moves through controls
- THEN focus indicators SHALL remain visible
- AND interactive order SHALL remain coherent

#### Scenario: Reduced motion preference
- GIVEN reduced motion is preferred
- WHEN animated transitions are present
- THEN non-essential motion SHALL be minimized or disabled
- AND usability SHALL remain equivalent
