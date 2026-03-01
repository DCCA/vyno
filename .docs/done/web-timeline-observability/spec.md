# Spec: Web Timeline Observability

### Requirement: Persisted Timeline Events
The system SHALL persist structured timeline events for digest runs initiated via Web APIs.

#### Scenario: Web-triggered run emits progress
- GIVEN an admin starts a digest run via Web
- WHEN runtime progress events are emitted
- THEN each event SHALL be persisted with run id, event index, stage, severity, message, elapsed time, and details payload

### Requirement: Live Timeline Access
The system SHALL provide timeline events during active runs.

#### Scenario: Admin views active run timeline
- GIVEN a run is active
- WHEN the admin opens the Timeline tab
- THEN the UI SHALL show recent timeline events for that run
- AND newly emitted events SHALL become visible on refresh polling

### Requirement: Historical Timeline Review
The system SHALL provide historical timeline retrieval for completed runs.

#### Scenario: Admin reviews prior run
- GIVEN one or more completed runs exist
- WHEN the admin selects a run in Timeline view
- THEN the UI SHALL render persisted events and summary data for that run

### Requirement: Timeline Filtering
The system SHALL support filtering timeline events by stage and severity.

#### Scenario: Admin filters noisy timeline
- GIVEN a run has many events
- WHEN the admin applies stage/severity filters
- THEN the event list SHALL include only matching entries

### Requirement: Timeline Ordering and Replay Control
The system SHALL support deterministic event ordering and operator control of live updates.

#### Scenario: Admin switches timeline ordering
- GIVEN a run has timeline events
- WHEN the admin selects newest-first or oldest-first order
- THEN the event list SHALL be returned in that order by the backend API

#### Scenario: Admin pauses live timeline updates
- GIVEN an active run is selected in Timeline view
- WHEN the admin pauses live polling
- THEN automatic refresh SHALL stop until polling is resumed

### Requirement: Run Notes for Improvement Loop
The system SHALL allow admins to save and view run-scoped notes.

#### Scenario: Admin records follow-up actions
- GIVEN an admin reviewed a run timeline
- WHEN they submit a timeline note
- THEN the note SHALL be stored and returned in subsequent note queries for that run

### Requirement: Timeline Export
The system SHALL provide timeline export for run-level postmortems.

#### Scenario: Admin exports run timeline
- GIVEN a run with timeline events exists
- WHEN the admin requests timeline export
- THEN the API SHALL return summary, events, and notes in one payload for archival/review
