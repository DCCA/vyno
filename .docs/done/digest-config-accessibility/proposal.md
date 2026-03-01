# Proposal: Digest Configuration Accessibility

## Why
Users need direct control over how strict digest filtering is, especially around seen-item behavior, without editing YAML or using CLI flags.

## Scope
- Add user-facing digest modes in Web.
- Add explicit seen policy controls.
- Add per-run override for `Run now`.
- Add digest restriction transparency for each run.
- Add safe seen-history maintenance actions.

## Out of Scope
- Replacing existing ranking/scoring algorithms.
- Changing source ingestion connectors.
- Multi-tenant RBAC redesign.

## Success Signals
- Users can change seen behavior from Web settings.
- Users can explain why a run was strict using funnel + reasons.
- Fewer empty or too-thin digests under strict modes.
