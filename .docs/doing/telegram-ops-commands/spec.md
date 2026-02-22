# Spec: Telegram Ops Commands

### Requirement: Authenticated Command Execution
The system SHALL execute Telegram commands only for authorized chat and user ids.

#### Scenario: Unauthorized command denied
- GIVEN a command from unauthorized chat or user
- WHEN the command is processed
- THEN no state-changing action is executed
- AND a denial response is returned

### Requirement: Manual Run Command
The system SHALL support triggering a manual digest run from Telegram.

#### Scenario: Run command accepted
- GIVEN an authorized admin message `/digest run`
- WHEN no run is currently active
- THEN a manual run is started
- AND the user receives run start and completion status

### Requirement: Source Management Commands
The system SHALL support source add/remove/list commands from Telegram.

#### Scenario: Add canonical github org source
- GIVEN `/source add github_org https://github.com/vercel-labs`
- WHEN command is processed
- THEN `vercel-labs` is persisted in local overlay
- AND duplicate canonical entries are not created

### Requirement: Overlay Merge
The system SHALL merge read-only base sources with mutable local overlay sources.

#### Scenario: Removed base source is masked
- GIVEN base config contains source A
- AND overlay marks source A as removed
- WHEN effective sources are loaded
- THEN source A is not included
