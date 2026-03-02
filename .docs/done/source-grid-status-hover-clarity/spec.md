# Spec: Source Grid Status Hover Clarity

### Requirement: Compact Desktop Columns
The desktop Sources grid SHALL render `Type`, `Source`, `Status`, and `Actions` as the primary columns.

#### Scenario: No horizontal overflow for actions
- GIVEN the operator opens Sources on desktop
- WHEN rows are rendered
- THEN `Edit` and `Delete` controls remain visible without requiring horizontal scrolling.

### Requirement: Diagnostics Discoverability
Row diagnostics SHALL remain available without persistent dense columns.

#### Scenario: Status hover detail
- GIVEN a row in the Sources grid
- WHEN the operator hovers or focuses the status indicator
- THEN the UI shows type, source, last seen, last error, and hint details.

### Requirement: Feature Parity
The redesign SHALL preserve add/remove, row edit/delete, filtering, status filter, and pagination behavior.

#### Scenario: Existing source operations remain intact
- GIVEN current source workflows
- WHEN the compact layout is used
- THEN all workflows complete with unchanged API behavior.
