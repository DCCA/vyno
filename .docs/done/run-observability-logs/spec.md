# Spec: Run Observability Logs

### Requirement: Structured File Logging
The system SHALL write structured JSON-line logs to a local log file.

#### Scenario: Log file is created
- GIVEN a digest run is executed
- WHEN logging is initialized
- THEN `logs/digest.log` exists (or configured path)
- AND each line is valid JSON

### Requirement: Run Correlation
Every log event SHALL include the run identifier.

#### Scenario: Run traceability
- GIVEN a run id `abc123`
- WHEN events are emitted during execution
- THEN log rows for that run include `run_id=abc123`

### Requirement: Stage Coverage
The system SHALL log key pipeline stages.

#### Scenario: Successful run stage events
- GIVEN a successful run
- WHEN logs are inspected
- THEN at minimum `run_start` and `run_finish` stages exist
- AND fetch/selection/delivery stages are present

### Requirement: Error Context
The system SHALL log error events with stage and failure context.

#### Scenario: Source fetch failure
- GIVEN a source fetch failure
- WHEN error is handled
- THEN an error log includes stage, source identifier, and error message

### Requirement: Configurable Logging
The system SHOULD allow runtime logging configuration via environment variables.

#### Scenario: Custom log path
- GIVEN `DIGEST_LOG_PATH=/tmp/digest.log`
- WHEN a run starts
- THEN logs are written to `/tmp/digest.log`

### Requirement: Log Rotation
The system SHALL support log rotation to bound local disk usage.

#### Scenario: Rotation settings apply
- GIVEN configured max size and backup count
- WHEN log size exceeds max size
- THEN rotated files are created according to backup count
