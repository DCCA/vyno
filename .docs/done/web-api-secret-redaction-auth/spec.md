# Spec: Web API Secret Redaction and Authentication

### Requirement: API Authentication SHALL Protect Config Endpoints
The web API SHALL require a valid API token for `/api/*` requests except health and CORS preflight checks.

#### Scenario: Missing token on protected endpoint
- GIVEN API auth mode is `required`
- WHEN a request is sent to a protected `/api/*` route without token
- THEN the API returns an authentication error
- AND the request does not reach endpoint business logic

#### Scenario: Health and preflight are accessible
- GIVEN API auth mode is enabled
- WHEN a request is sent to `/api/health` or an `OPTIONS` preflight
- THEN the request bypasses token validation

### Requirement: Secret Fields SHALL Be Redacted in Read APIs
The web API SHALL not return plaintext secret-like values in profile/config read responses.

#### Scenario: Profile read response
- GIVEN effective profile contains token-like values
- WHEN `GET /api/config/profile` is called
- THEN secret fields are returned as redacted placeholders

### Requirement: Secret Fields SHALL Be Redacted in Snapshots
Config history snapshots SHALL not persist plaintext secret-like values.

#### Scenario: Snapshot creation after config mutation
- GIVEN source/profile mutation triggers snapshot save
- WHEN snapshot payload is written to history
- THEN secret-like fields are redacted before write

### Requirement: Redacted Values SHALL Not Break Save/Validate/Diff
The system SHALL preserve existing secret values when redacted placeholders are posted back.

#### Scenario: Profile save with redacted placeholders
- GIVEN client submits profile payload that includes redacted placeholders
- WHEN save/validate/diff endpoint processes payload
- THEN placeholders are replaced with current effective secret values
- AND non-secret edits are still applied normally
