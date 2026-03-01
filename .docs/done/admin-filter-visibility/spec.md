# Spec: Admin Filter Visibility

### Requirement: Stage-Level Filter Accountability
The system SHALL report run-level counts for major filtering stages so operators can explain candidate attrition.

#### Scenario: Incremental run drops most items
- GIVEN a run executes in incremental mode
- WHEN context metadata is generated
- THEN context SHALL include dropped counts for dedupe, window, seen, blocked, and ranked-out stages
- AND context SHALL include low-impact GitHub issue drop counts

### Requirement: Video Funnel Observability
The system SHALL report video counts across pipeline stages.

#### Scenario: Videos are fetched but not selected
- GIVEN at least one video is fetched during ingest
- WHEN run context is produced
- THEN context SHALL include video counts for fetched, post-window, post-seen, post-block, and selected
- AND operators SHALL be able to identify the stage where video count drops to zero

### Requirement: Operator-Facing Context Rendering
The system SHALL render filter breakdown and video funnel metrics in delivery context sections.

#### Scenario: Admin inspects Obsidian note
- GIVEN a completed run with context metadata
- WHEN the Obsidian note is rendered
- THEN the Context section SHALL show dropped-stage totals and video funnel totals

#### Scenario: Admin inspects Telegram digest message
- GIVEN a completed run with context metadata
- WHEN the Telegram message is rendered
- THEN the Context section SHALL show dropped-stage totals and video funnel totals
