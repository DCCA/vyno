# Proposal: Onboarding Setup Flow

## Why
New operators can run the digest today, but the first-time setup path still depends on reading multiple docs, editing raw files, and guessing failure causes. This increases time-to-first-good-digest and creates avoidable support friction.

## Scope
- Add a guided onboarding flow in the existing web console.
- Add a CLI preflight command for headless/operator-first setup (`digest doctor`).
- Add preflight checks for config/env/path readiness with actionable hints.
- Add source pack selection to speed initial source setup.
- Add safe preview execution that does not mutate production run state.
- Add activation + health confirmation steps in onboarding status.
- Persist onboarding progress for resume behavior.

## Out of Scope
- Multi-user auth/RBAC and internet-exposed hardening.
- Replacing existing source/profile tabs and workflows.
- Scoring/ranking model redesign.
- Hosted deployment automation.
