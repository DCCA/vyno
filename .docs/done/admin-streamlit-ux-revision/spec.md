# Spec: Admin Streamlit UX Revision

### Requirement: Overview Dashboard
The admin Streamlit UI SHALL provide an overview page with key operational metrics and primary actions.

#### Scenario: Admin opens dashboard
- GIVEN an authenticated admin session
- WHEN the admin lands on `Overview`
- THEN the UI shows bot state, run count, source count, and feedback count
- AND the UI exposes primary actions for `run now` and bot restart

### Requirement: Guided Source Management
The UI SHALL provide type-aware source add/remove workflows.

#### Scenario: Add source with canonical preview
- GIVEN an authenticated admin on `Sources`
- WHEN the admin selects a source type and enters a value
- THEN the UI shows canonicalized preview or validation feedback before submit
- AND submit executes through `AdminService.add_source`

#### Scenario: Remove existing source safely
- GIVEN effective sources exist for a selected type
- WHEN the admin chooses a value from the current list and removes it
- THEN submit executes through `AdminService.remove_source`
- AND UI refreshes to show updated effective list

### Requirement: Improved Operational Readability
The UI SHALL improve readability for runs, logs, outputs, and feedback.

#### Scenario: Runs filtering
- GIVEN run rows with mixed statuses
- WHEN admin applies status filters
- THEN only matching rows are shown in a table optimized for scanning

#### Scenario: Logs inspection
- GIVEN logs exist
- WHEN admin filters by run/stage/level
- THEN rows are shown in a structured table
- AND raw JSON remains available in a collapsible section

#### Scenario: Output preview
- GIVEN output previews are available
- WHEN admin opens `Outputs`
- THEN Telegram and Obsidian previews appear in separate tabs
- AND each preview shows content length and rendered code block

### Requirement: No Backend Regression
The UX revision SHALL NOT change backend control semantics.

#### Scenario: Regression validation
- GIVEN existing admin behavior tests
- WHEN the test suite is executed after UI revision
- THEN tests pass without introducing failures in admin service behavior
