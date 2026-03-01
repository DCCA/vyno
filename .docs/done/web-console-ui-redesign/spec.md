# Spec: Web Console UI Redesign (No Regression)

### Requirement: Feature Parity Preservation
The redesigned Web UI SHALL preserve all existing functional capabilities and operator workflows.

#### Scenario: Existing action coverage remains available
- GIVEN a user uses the redesigned UI
- WHEN they need any current capability (onboarding, run-now, source management, digest policy, timeline review, rollback, seen reset)
- THEN the capability SHALL remain accessible in the UI
- AND the action SHALL call the same backend contract semantics as before

#### Scenario: No loss of admin safety controls
- GIVEN destructive or sensitive controls exist in the current UI
- WHEN redesign is delivered
- THEN confirmation and safety affordances SHALL remain available
- AND audit-relevant workflows SHALL remain intact

### Requirement: Loading, Progress, and Error Fidelity
The redesigned Web UI SHALL keep existing loading/progress/error state behavior for all async operations.

#### Scenario: Run-now loading feedback
- GIVEN a user starts `Run now`
- WHEN the request is in-flight
- THEN the UI SHALL show an explicit loading state
- AND completion/failure SHALL produce clear success/error feedback

#### Scenario: Live progress visibility
- GIVEN a run is active
- WHEN progress updates are received
- THEN the UI SHALL show current stage, status, and relevant progress detail
- AND polling behavior SHALL continue to update without full-page interruption

### Requirement: Intentional Motion and Animation
The redesigned Web UI SHALL include purposeful motion that supports hierarchy and state change comprehension.

#### Scenario: Page and section entry transitions
- GIVEN a user navigates between primary console sections
- WHEN content is rendered
- THEN the UI SHALL animate entry transitions for major layout regions
- AND animations SHALL be short and non-blocking

#### Scenario: Reduced motion support
- GIVEN a user prefers reduced motion
- WHEN the UI renders animated affordances
- THEN animations SHALL be reduced or disabled
- AND usability SHALL remain equivalent

### Requirement: Information Hierarchy and Navigation
The redesigned Web UI SHALL organize the console into focused surfaces with clear separation between daily operations and advanced controls.

#### Scenario: Operator prioritizes run health
- GIVEN a user opens the console
- WHEN the main landing view loads
- THEN run health, alerts, and primary actions SHALL be visible without deep scrolling
- AND advanced controls SHALL not dominate initial viewport

#### Scenario: Advanced operations remain discoverable
- GIVEN a user needs timeline/history/rollback tasks
- WHEN navigating the redesign
- THEN these tasks SHALL remain reachable through explicit navigation
- AND contextual labels SHALL make intended usage clear

### Requirement: Responsive and Accessible UI
The redesigned Web UI SHALL remain usable across desktop and mobile breakpoints with clear keyboard and focus behavior.

#### Scenario: Mobile width access
- GIVEN a user accesses the UI at small viewport widths
- WHEN interacting with core flows
- THEN controls SHALL remain operable without content overlap or clipping
- AND primary actions SHALL remain reachable

#### Scenario: Keyboard and focus usage
- GIVEN a keyboard-only user navigates controls
- WHEN focus moves across interactive elements
- THEN visible focus indicators SHALL be present
- AND interaction order SHALL remain coherent

### Requirement: Safe Migration and Verification
The redesign rollout SHALL be delivered in incremental, testable phases.

#### Scenario: Incremental merge without feature breakage
- GIVEN redesign implementation is in progress
- WHEN a phase is completed
- THEN build and regression checks SHALL pass before proceeding
- AND unresolved regressions SHALL block next-phase implementation
