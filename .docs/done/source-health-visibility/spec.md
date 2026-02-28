# Spec: Source Health Visibility

### Requirement: Latest Completed Run SHALL Expose Source Error Details
The API SHALL return parsed source errors for the latest completed run.

#### Scenario: Latest completed run has source failures
- GIVEN source error lines are stored for a completed run
- WHEN `/api/run-status` is requested
- THEN response SHALL include structured source error entries with source kind, source id, raw error, and hint

### Requirement: Source Health SHALL Aggregate Recent Failures
The API SHALL expose aggregated source failure frequencies across recent runs.

#### Scenario: Source repeatedly fails across runs
- GIVEN the same source error appears in multiple runs
- WHEN `/api/source-health` is requested
- THEN response SHALL include count and latest error context for that source
