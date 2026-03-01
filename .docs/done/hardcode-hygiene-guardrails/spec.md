# Spec: hardcode-hygiene-guardrails

## Requirement: Shared runtime constants
The backend SHALL define shared defaults in one module to reduce drift and magic values.

### Scenario: Constants used across modules
- Given repeated literals for model, limits, and runtime defaults
- When runtime/config modules import constants
- Then behavior remains unchanged and duplicated literal definitions are reduced

## Requirement: UI/API startup decoupling
Local UI/API startup MUST support explicit bind/public host behavior and token propagation.

### Scenario: Local app startup with required API auth
- Given API auth mode is `required` and no token is provided
- When `make app` is executed
- Then startup generates a session token, starts API/UI, and injects matching token/header into both processes

### Scenario: UI API base resolution
- Given `VITE_API_BASE` is not set
- When UI issues API requests
- Then requests use relative `/api/*` paths (same-origin/proxy friendly)

## Requirement: Security regression gate
Repository checks MUST block high-risk regressions while allowing incremental adoption.

### Scenario: CI security checks
- Given a pull request run
- When the security workflow executes
- Then it SHALL run detect-secrets baseline check, Bandit high-severity scan, Ruff safety syntax checks, and Semgrep advisory scan

### Scenario: Local developer workflow
- Given an engineer preparing a change
- When `make security-check` is executed
- Then local checks SHALL match the CI blocking checks
