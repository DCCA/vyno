# Spec: CORS Preflight Localhost Fix

### Requirement: Local Dev Origins SHALL Pass Preflight
The web API SHALL accept browser preflight requests from local development origins on arbitrary ports.

#### Scenario: Vite dev server picks an alternate port
- GIVEN the frontend origin is `http://127.0.0.1:5174`
- WHEN browser sends preflight `OPTIONS` for API routes
- THEN CORS origin matching succeeds
- AND API requests can proceed without transport failures

### Requirement: CORS Scope SHALL Stay Local by Default
The default CORS policy SHALL remain limited to localhost/private-network style development origins.

#### Scenario: External public origin request
- GIVEN a non-local public origin
- WHEN CORS origin matching is evaluated
- THEN the origin is rejected by default policy

### Requirement: CORS Configuration SHALL Be Test-Covered
The implementation SHALL include automated tests for origin matching and applied middleware settings.

#### Scenario: Regression test execution
- GIVEN the test suite is run
- WHEN CORS tests execute
- THEN localhost variable-port origins are accepted
- AND non-local origins are rejected
