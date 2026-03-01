# Spec: Admin Review Diff UX

### Requirement: Live Local Diff Visibility
The console SHALL display pending profile changes without requiring a server round-trip.

#### Scenario: Operator edits profile controls
- GIVEN the profile editor content differs from the loaded effective profile
- WHEN the operator opens the Review tab
- THEN the UI SHALL show a non-empty local diff preview

### Requirement: Clear Server Diff State
The console SHALL distinguish between "not computed yet" and "computed empty diff".

#### Scenario: Operator has not requested server diff
- GIVEN no server diff request has been made
- WHEN the Review tab renders server diff section
- THEN the UI SHALL show guidance to run Compute Diff

#### Scenario: Server diff computed and empty
- GIVEN Compute Diff was executed successfully
- WHEN server returns an empty diff object
- THEN the UI SHALL show that editor payload matches effective profile

### Requirement: JSON Validation Guardrails
The console SHALL prevent review actions when profile JSON is invalid.

#### Scenario: Invalid JSON in advanced editor
- GIVEN profile JSON cannot be parsed as an object
- WHEN the Review tab renders
- THEN the UI SHALL show an error alert
- AND Validate, Compute Diff, and Save Overlay actions SHALL be disabled

