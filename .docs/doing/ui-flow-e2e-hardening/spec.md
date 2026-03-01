# Spec: ui-flow-e2e-hardening

### Requirement: Web POST endpoints remain callable from UI
All web UI POST endpoints SHALL accept valid JSON payloads without internal model-definition errors.

#### Scenario: Source mutation request
- GIVEN web UI posts source add/remove payloads
- WHEN API handles request body
- THEN endpoint responds with non-500 status for valid payloads

#### Scenario: Source pack apply request
- GIVEN web UI posts onboarding source-pack payload
- WHEN API handles request body
- THEN endpoint responds with non-500 status for valid payloads

### Requirement: UI flow verification
Core web UI flows SHALL be exercised in a real browser session.

#### Scenario: Operator setup workflow
- GIVEN API and UI are running
- WHEN operator uses onboarding, sources, review, and history flows
- THEN actions complete without transport-layer fetch failures
