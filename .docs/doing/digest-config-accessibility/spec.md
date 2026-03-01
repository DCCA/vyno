# Spec: Digest Configuration Accessibility

### Requirement: User-Configurable Digest Modes
The system SHALL provide user-facing digest modes that map to runtime filtering behavior.

#### Scenario: User sets default mode
- GIVEN a user opens digest settings
- WHEN they choose a default mode and save
- THEN the system SHALL persist that mode as the default for future Web-triggered runs
- AND the saved mode SHALL be visible in settings and run metadata

#### Scenario: User overrides mode for a single run
- GIVEN a default mode is configured
- WHEN the user starts `Run now` with a one-time mode override
- THEN the system SHALL apply the override only to that run
- AND subsequent runs SHALL use the saved default mode

### Requirement: Seen Policy Controls
The system SHALL expose clear seen-policy options that control how previously seen items are treated.

#### Scenario: Strict new-content mode
- GIVEN the user selects `Fresh Only`
- WHEN a run is executed
- THEN the runtime SHALL use unseen candidates only
- AND broad seen fallback SHALL be disabled

#### Scenario: Balanced fallback mode
- GIVEN the user selects `Balanced`
- WHEN a run is executed with insufficient unseen candidates
- THEN the runtime SHALL allow seen fallback according to policy
- AND run metadata SHALL indicate fallback usage

### Requirement: Restriction Transparency
The system SHALL expose run restrictiveness and stage-level filtering attribution.

#### Scenario: User inspects a strict run
- GIVEN a run completed with high attrition
- WHEN the user opens run review in Web
- THEN the UI SHALL show a strictness level (`Low`, `Medium`, or `High`)
- AND the UI SHALL show filter funnel counts (`fetched -> post_window -> post_seen -> post_block -> selected`)
- AND the UI SHALL show top restriction reasons

#### Scenario: User needs action guidance
- GIVEN strictness is `High`
- WHEN the run summary is displayed
- THEN the system SHALL provide at least one actionable recommendation (for example: use `Balanced`, replay recent, or reset seen history)

### Requirement: Safe Seen-History Maintenance
The system SHALL allow admin-safe maintenance of seen history with explicit confirmation and auditability.

#### Scenario: User previews a seen reset
- GIVEN a user opens seen maintenance controls
- WHEN they request a dry run reset preview
- THEN the system SHALL return affected counts before any destructive change

#### Scenario: User executes seen reset
- GIVEN a user confirms a reset action
- WHEN the reset is executed
- THEN the system SHALL record an audit event with actor, action type, and scope
- AND subsequent runs SHALL reflect updated seen state

### Requirement: Backward Compatibility
The system SHALL preserve existing behavior when no new policy is configured.

#### Scenario: Existing installation without new settings
- GIVEN an installation upgrades to this feature
- WHEN no explicit mode has been saved
- THEN the runtime SHALL use current default Web behavior
- AND existing API clients SHALL continue working
