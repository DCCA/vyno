# Spec: Simple App Start Command

### Requirement: One Command SHALL Start the Local Web App
The system SHALL provide a single command that starts both local web API and web UI.

#### Scenario: User starts the app from repository root
- GIVEN the user is in project root
- WHEN the user runs `make app`
- THEN the web API starts on local host and port
- AND the web UI starts in dev mode
- AND startup output includes where to open the UI

### Requirement: Startup SHALL Fail Fast with Helpful Hints
The startup flow SHALL surface clear guidance when required tools are missing.

#### Scenario: Node or npm is missing
- GIVEN the machine does not have `npm`
- WHEN `make app` runs
- THEN the command exits non-zero
- AND prints a direct dependency/install hint

### Requirement: Shutdown SHALL Be Clean
The startup flow SHALL stop child processes when the main command exits.

#### Scenario: User presses Ctrl+C
- GIVEN API and UI are running via `make app`
- WHEN the user interrupts the command
- THEN the API process is stopped
- AND no orphan process is left behind by the startup script

### Requirement: Docs SHALL Advertise One-Command Startup
The README SHALL document the one-command startup flow.

#### Scenario: User follows onboarding docs
- GIVEN a new user opens README
- WHEN they reach web console instructions
- THEN they see `make app` as the default easy path
