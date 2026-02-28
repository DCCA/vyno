# Spec: Onboarding Setup Flow

### Requirement: Guided Onboarding Entry Point
The system SHALL provide a single onboarding entry point in the web console and a CLI-equivalent readiness command.

#### Scenario: Operator starts onboarding
- GIVEN a repository clone with default config files
- WHEN the operator opens the onboarding tab or runs `digest doctor`
- THEN the system returns ordered setup steps with status
- AND each failed check includes actionable remediation guidance

### Requirement: Preflight Validation
The system SHALL validate environment, config, and filesystem prerequisites before activation.

#### Scenario: Required secret missing
- GIVEN profile/runtime settings require OpenAI access
- WHEN preflight runs without `OPENAI_API_KEY`
- THEN preflight marks the check as failed
- AND preflight includes a hint describing how to resolve it

#### Scenario: Optional integration missing
- GIVEN GitHub sources are configured without `GITHUB_TOKEN`
- WHEN preflight runs
- THEN preflight marks the check as warning
- AND setup can continue with explicit rate-limit warning

### Requirement: Source Bootstrap Presets
The system SHALL provide curated source packs to accelerate initial source setup.

#### Scenario: Apply a source pack
- GIVEN an onboarding source pack is selected
- WHEN the operator applies the pack
- THEN sources are added through existing canonicalization logic
- AND overlay writes are preserved with snapshot history

### Requirement: Safe Preview Run
The system SHALL support preview digest generation without production state mutation.

#### Scenario: Preview execution
- GIVEN onboarding is in progress
- WHEN the operator triggers preview
- THEN the system returns digest preview artifacts (Telegram chunks and Obsidian note)
- AND the system MUST NOT send Telegram messages
- AND the system MUST NOT write to production DB run history

### Requirement: Activation and Health Confirmation
The system SHALL provide a go-live action and immediate health visibility.

#### Scenario: Activate from onboarding
- GIVEN onboarding preflight has been run
- WHEN the operator triggers activation
- THEN a live run request is started with run-lock protection
- AND onboarding status includes latest run health details

### Requirement: Resume Progress
The system SHOULD persist onboarding progress across sessions.

#### Scenario: Resume setup after interruption
- GIVEN an operator completes some onboarding steps
- WHEN they return later
- THEN previously completed steps remain marked complete
- AND pending steps remain visible until completed
