# Spec: UI Loading Affordances

### Requirement: Actions SHALL Expose Loading State
The web UI SHALL provide visible loading feedback while asynchronous actions are in progress.

#### Scenario: Operator triggers a long-running action
- GIVEN the operator clicks preview/run/save/rollback actions
- WHEN the request is in progress
- THEN the UI shows a loading indicator and contextual label

### Requirement: Loading Feedback SHALL Work in Setup and Manage Modes
Loading affordances SHALL appear consistently across both mode surfaces.

#### Scenario: Setup mode action
- GIVEN setup mode is active
- WHEN preflight/preview/source-pack action starts
- THEN loading state is visible in-button and globally

#### Scenario: Manage mode action
- GIVEN manage mode is active
- WHEN source/review/rollback action starts
- THEN loading state is visible in-button and globally
