# Completion Summary

## What Changed
- Added a workspace-level onboarding lifecycle (`needs_setup` vs `ready`) to the onboarding status payload.
- Made the primary navigation lifecycle-aware so first-run workspaces see setup-focused surfaces, while returning workspaces no longer show onboarding in the main menu.
- Added a hidden `Revisit setup guide` action in Profile maintenance tools that reopens setup without resetting the workspace.
- Updated the setup page and dashboard copy to distinguish activation from recurring product usage, including a milestone summary and revisit banner.

## Validation
- `python3 -m unittest tests.test_onboarding -v`
- `npm --prefix web run test`
- `npm --prefix web run build`

## Risks
- Direct deep links to hidden surfaces remain possible; this change focuses on primary navigation and product framing, not hard route denial.
- Revisit mode is intentionally non-destructive and does not reset progress or config.

## Follow-Up
- If the product later adds real user accounts, lifecycle should move from workspace-wide state to per-user onboarding state.
- A destructive factory reset for setup should be a separate admin-only change, not part of revisit mode.
