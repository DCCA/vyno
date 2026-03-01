# Spec: Dockerize Bot Runtime

### Requirement: Reproducible Container Runtime
The system SHALL provide a container image that runs the existing `digest` CLI commands without code path divergence from local execution.

#### Scenario: Bot command runs in container
- GIVEN the project image is built from repository source
- WHEN the container starts with command `digest bot`
- THEN the bot worker starts successfully
- AND command behavior matches local CLI semantics

### Requirement: Persistent Runtime State
The system SHALL persist mutable runtime artifacts outside the container filesystem.

#### Scenario: Restart preserves operational state
- GIVEN the container is recreated
- WHEN runtime paths are mounted as volumes
- THEN `digest.db`, logs, source overlay, and run lock files remain available
- AND bot/admin operations continue with prior state

### Requirement: Automatic Recovery
The deployment SHALL auto-restart bot workloads after process exit or host reboot.

#### Scenario: Bot process crashes
- GIVEN a running bot container with restart policy enabled
- WHEN the bot process exits unexpectedly
- THEN the container runtime restarts it automatically
- AND the bot resumes long-poll processing

#### Scenario: Host reboots
- GIVEN Docker service is configured to start on boot
- WHEN the host reboots
- THEN the bot container returns to running state without manual intervention

### Requirement: Operational Health Signals
The system SHALL expose basic health and debugging signals for runtime operations.

#### Scenario: Operator validates bot health
- GIVEN bot container is running
- WHEN the operator checks logs and container status
- THEN they can determine whether polling is active and whether recent errors occurred
- AND a documented healthcheck command is available

### Requirement: Secrets and Config Separation
The deployment SHALL load runtime secrets via environment and keep configuration files mountable/editable.

#### Scenario: Secrets rotation
- GIVEN bot credentials are provided via `.env` or environment injection
- WHEN secrets are updated and container is recreated
- THEN new secrets are applied without image rebuild
- AND secrets are not embedded in the image layers
