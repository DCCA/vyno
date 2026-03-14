# Spec: X Budget Per Run

### Requirement: Hard X Spend Cap
The system SHALL derive a hard X post budget per run from operator-configured cost and spend limits.

#### Scenario: Standard budget
- GIVEN `x_cost_per_post_usd = 0.005`
- AND `x_max_spend_per_run_usd = 0.05`
- WHEN a run starts
- THEN the system SHALL derive an X budget of `10` posts for that run

### Requirement: Author-First Allocation
The system SHALL allocate the X post budget to `x_author` selectors before `x_theme` selectors.

#### Scenario: Authors and themes are both configured
- GIVEN at least one `x_author` and one `x_theme`
- AND a positive X post budget
- WHEN selector limits are planned
- THEN the system SHALL allocate the budget across authors first
- AND any themes that receive zero budget SHALL be skipped without failing the run

### Requirement: Zero Budget Skips X Cleanly
The system SHALL skip X selector fetching cleanly when the derived X post budget is zero.

#### Scenario: Spend cap disables X
- GIVEN `x_max_spend_per_run_usd = 0`
- WHEN a run starts
- THEN the system SHALL not call the X selector API
- AND the run SHALL continue normally for non-X sources

### Requirement: Budget Visibility
The system SHALL expose the configured X budget and derived post budget to operators.

#### Scenario: Profile review
- GIVEN the operator opens profile controls
- WHEN X budget settings are present
- THEN the UI SHALL show both the per-post cost and max spend values
- AND the UI SHALL show the derived maximum posts per run
