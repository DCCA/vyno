# Spec

### Requirement: Default Docker Stack
The default Docker startup workflow SHALL start both the Telegram bot service and the scheduler/web service.

#### Scenario: New user starts Docker
- GIVEN a user runs `make docker-up`
- WHEN startup completes successfully
- THEN both `digest-bot` and `digest-scheduler` SHALL be started
- AND Telegram admin commands SHALL be available without requiring a second startup command

### Requirement: Default Docker Build Alignment
The default Docker build workflow SHALL build the same services that the default startup workflow uses.

#### Scenario: Build before startup
- GIVEN a user runs `make docker-build`
- WHEN the build finishes
- THEN both `digest-bot` and `digest-scheduler` images SHALL be built
- AND `make docker-up` SHALL NOT depend on an unbuilt scheduler image

### Requirement: Persistence Documentation
The Docker documentation SHALL describe that operator changes persist across restarts because the runtime state is host-mounted.

#### Scenario: Source added through bot or app
- GIVEN a user adds sources or updates config through the bot or web app
- WHEN Docker containers restart
- THEN the documentation SHALL state that mounted paths preserve those changes
- AND the persisted paths SHALL include config overlays, runtime state, and the SQLite database
