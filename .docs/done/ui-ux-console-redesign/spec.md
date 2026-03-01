# Spec: UI UX Console Redesign

### Requirement: Setup Journey SHALL Be Task-First
The web console SHALL present a setup-first mode that prioritizes ordered onboarding steps over tab navigation.

#### Scenario: First-time operator opens the console
- GIVEN onboarding is incomplete
- WHEN the operator loads the console
- THEN the primary view highlights setup progress and next actions
- AND onboarding actions are available without visiting advanced tabs

### Requirement: Manage Workspace SHALL Remain Available
The system SHALL provide a dedicated advanced workspace for source, profile, review, and rollback operations.

#### Scenario: Operator performs day-2 maintenance
- GIVEN the operator needs to update runtime configuration
- WHEN they switch to manage mode
- THEN source, profile, review, and history tools are available
- AND all existing mutation semantics remain unchanged

### Requirement: Visual System SHALL Improve Operational Clarity
The UI SHALL use a coherent design system with explicit status hierarchy, readable typography, and responsive layout.

#### Scenario: Operator checks run and setup health
- GIVEN run status and onboarding status are available
- WHEN the console renders summary and status areas
- THEN status badges and progress states are visually distinct
- AND the layout remains readable on desktop and mobile widths

### Requirement: Existing Operations SHALL Continue End-to-End
The redesign SHALL preserve all existing API-connected actions.

#### Scenario: Operator executes full workflow
- GIVEN the redesigned console
- WHEN the operator runs preflight, applies source packs, edits sources/profile, previews, activates, validates/diffs/saves, and rolls back
- THEN each action completes through existing endpoints
- AND no transport-level `Failed to fetch` errors occur due to UI regressions

### Requirement: Verification SHALL Include Real Browser E2E
The change SHALL be validated with test/build checks and browser-driven flow execution.

#### Scenario: Release verification
- GIVEN the redesign implementation is complete
- WHEN verification runs
- THEN `make test` passes
- AND `make web-ui-build` passes
- AND browser automation confirms critical UI flows are operable
