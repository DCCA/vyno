# Spec: Docker Obsidian Path Override

### Requirement: Docker Vault Path Override
The system SHALL allow Docker to override the configured Obsidian vault path with the mounted in-container path.

#### Scenario: Docker run with mounted vault
- GIVEN the profile YAML contains a host-local Obsidian vault path
- AND Docker provides `OBSIDIAN_VAULT_PATH=/app/obsidian-vault`
- WHEN the profile is parsed inside the container
- THEN the effective Obsidian vault path SHALL be `/app/obsidian-vault`

### Requirement: Local Behavior Preservation
The system SHALL preserve current local non-Docker behavior when the Docker override env var is absent.

#### Scenario: Local run without override env
- GIVEN the profile YAML contains the current local vault path
- AND `OBSIDIAN_VAULT_PATH` is not set
- WHEN the profile is parsed
- THEN the effective Obsidian vault path SHALL remain the YAML value

### Requirement: Docker Services Export Override
The Docker services SHALL provide the mounted vault path override to the application process.

#### Scenario: Compose configuration
- GIVEN the bot and scheduler services are started from Compose
- WHEN their environment is inspected
- THEN both services SHALL include `OBSIDIAN_VAULT_PATH=/app/obsidian-vault`

### Requirement: Persisted Obsidian Delivery
The Docker digest run SHALL write notes into the host-mounted Obsidian vault.

#### Scenario: Real Docker digest
- GIVEN Docker services are running with the override
- WHEN a digest run writes an Obsidian note
- THEN the note SHALL appear under the host `obsidian-vault/` directory
- AND the file SHALL remain after container restart
