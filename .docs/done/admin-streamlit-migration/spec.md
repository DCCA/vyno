# Spec: Admin Streamlit Migration

### Requirement: Streamlit Admin Launch
The system SHALL provide a CLI command to launch the Streamlit admin app.

#### Scenario: Launch command
- GIVEN valid local environment
- WHEN `digest admin-streamlit` is executed
- THEN Streamlit starts with configured host/port and app path

### Requirement: Auth-Gated UI
The Streamlit UI SHALL require admin login before showing operational controls.

#### Scenario: Unauthenticated state
- GIVEN no admin session in Streamlit state
- WHEN app renders
- THEN only login form is shown

### Requirement: Operational Parity
The Streamlit UI SHALL support existing admin operations via `AdminService`.

#### Scenario: Source mutation from UI
- GIVEN admin is logged in
- WHEN source add/remove is submitted
- THEN operation executes through `AdminService` and audit is recorded
