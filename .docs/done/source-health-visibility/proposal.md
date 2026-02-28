# Proposal: Source Health Visibility in Web Console

## Why
Operators need to know which sources are failing so they can fix credentials, URLs, or connectivity issues quickly. Error counts alone are insufficient.

## Scope
- Expose structured source error details from latest completed run.
- Add aggregated source health endpoint over recent runs.
- Render broken source table with actionable hints in web UI.

## Out of Scope
- Automatic remediation.
- External alerting integrations.
