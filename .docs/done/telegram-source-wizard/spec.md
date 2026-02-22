# Spec: Telegram Source Wizard (Inline Buttons)

### Requirement: Wizard Entry
The system SHALL provide a button-guided source management flow.

#### Scenario: Start wizard
- GIVEN an authorized user
- WHEN `/source wizard` is sent
- THEN bot returns inline action buttons for source management

### Requirement: Callback Query Routing
The system SHALL process Telegram callback queries for wizard interactions.

#### Scenario: Select action and type
- GIVEN wizard action buttons are shown
- WHEN user taps an action and source type
- THEN bot updates flow state and prompts for value or executes list flow

### Requirement: Confirmed Mutations
The system SHALL require explicit confirmation before add/remove mutation.

#### Scenario: Confirm add
- GIVEN user entered a valid source value in wizard
- WHEN user taps Confirm
- THEN source mutation is executed with canonicalization/idempotency rules

### Requirement: Compatibility
The system SHALL preserve existing text command behaviors.

#### Scenario: Existing `/source add` command
- GIVEN text command users
- WHEN `/source add <type> <value>` is sent
- THEN behavior remains unchanged
