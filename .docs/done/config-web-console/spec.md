# Spec: Config Web Console

### Requirement: Source Management SHALL Be Guided
The console SHALL allow source add/remove with canonicalization and overlay-safe writes.

#### Scenario: Add source from UI
- GIVEN an operator enters source type/value
- WHEN add is submitted
- THEN canonicalization SHALL be applied through existing source registry logic
- AND update SHALL persist to sources overlay

### Requirement: Profile Edits SHALL Use Overlay
The console SHALL write profile updates to `data/profile.local.yaml` as an overlay over tracked base profile.

#### Scenario: Save profile draft
- GIVEN an operator edits profile values in UI
- WHEN save is submitted
- THEN server SHALL validate profile payload
- AND persist only changed overlay fields

### Requirement: Review Before Apply SHALL Be Available
The console SHALL support validation and diff preview prior to saving profile changes.

#### Scenario: Validate and diff
- GIVEN a profile draft exists in UI
- WHEN operator requests validation and diff
- THEN server SHALL return normalized profile payload and changed keys

### Requirement: Run Control SHALL Include Run Now
The console SHALL expose manual run trigger and current/last run status.

#### Scenario: Trigger run from UI
- GIVEN no active run lock
- WHEN operator clicks run now
- THEN run starts in background and lock state updates

### Requirement: Rollback SHALL Be Available
The console SHALL store config snapshots and support rollback to a prior snapshot.

#### Scenario: Roll back configuration
- GIVEN snapshot history exists
- WHEN operator selects rollback for a snapshot
- THEN overlay files SHALL revert to snapshot state
