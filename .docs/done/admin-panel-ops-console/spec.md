# Spec: Admin Panel Ops Console

### Requirement: Authenticated Access
The system SHALL restrict admin panel access to authenticated admins.

#### Scenario: Unauthorized request
- GIVEN a request without a valid admin session
- WHEN protected admin endpoints are accessed
- THEN access is denied
- AND no state-changing action is executed

### Requirement: Source Management
The system SHALL provide source add/remove/list operations through the panel using existing canonicalization rules.

#### Scenario: Add GitHub org URL
- GIVEN admin enters `https://github.com/vercel-labs`
- WHEN source type is `github_org` and add is submitted
- THEN canonical `vercel-labs` is persisted
- AND duplicates are not created

#### Scenario: Remove base source
- GIVEN a source exists in base config
- WHEN admin removes it via panel
- THEN removal is represented via overlay tombstone
- AND effective source list excludes it

### Requirement: Bot Lifecycle Visibility and Control
The system SHALL show bot status and support safe start/stop/restart actions.

#### Scenario: Bot status view
- GIVEN admin opens lifecycle page
- WHEN status is requested
- THEN panel shows running state, pid (if present), and last heartbeat/time

#### Scenario: Safe bot stop
- GIVEN bot is running
- WHEN admin clicks stop
- THEN stop command is executed via restricted control path
- AND action is audit logged

### Requirement: Manual Run Control
The system SHALL allow admins to trigger manual digest runs and view run state.

#### Scenario: Trigger run while idle
- GIVEN no active run lock
- WHEN admin clicks run now
- THEN run starts and run id/status are displayed

#### Scenario: Trigger run while active
- GIVEN active run lock exists
- WHEN admin clicks run now
- THEN request is rejected with active run metadata

### Requirement: Log Inspection
The system SHALL provide log inspection with filtering.

#### Scenario: Filter logs by run and stage
- GIVEN logs exist
- WHEN admin filters by `run_id` and `stage`
- THEN matching log rows are returned in descending time order

### Requirement: Output Inspection
The system SHALL provide recent output visibility.

#### Scenario: Obsidian output preview
- GIVEN a completed run wrote an Obsidian note
- WHEN admin opens output view
- THEN panel shows path and rendered note preview

### Requirement: Feedback Capture
The system SHALL store admin quality feedback per run/item.

#### Scenario: Submit item feedback
- GIVEN an item in output view
- WHEN admin submits rating and optional comment
- THEN feedback is persisted with run_id/item_id/timestamp

### Requirement: Audit Trail
The system SHALL record admin actions for critical operations.

#### Scenario: Source mutation audit
- GIVEN admin adds/removes a source
- WHEN operation completes
- THEN audit record contains actor, action, target, and timestamp
