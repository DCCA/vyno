# Spec: Bootstrap Firehose Workflow

### Requirement: Documentation Workspace Exists
The repository SHALL include a `.docs/` workspace with `todo`, `doing`, and `done` directories.

#### Scenario: Base structure is present
- GIVEN a fresh clone of the repository
- WHEN a contributor inspects `.docs/`
- THEN `todo`, `doing`, and `done` directories exist

### Requirement: PRD Entry Point Exists
The repository SHALL include `.docs/PRD.md` as the context entry point.

#### Scenario: PRD is discoverable
- GIVEN a contributor onboarding to the project
- WHEN they open `.docs/PRD.md`
- THEN they can find goals, constraints, and non-goals sections
