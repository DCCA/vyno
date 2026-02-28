# Spec: Online Must-read Quality Repair

### Requirement: Runtime SHALL Judge Must-read Quality Online
The system SHALL evaluate Must-read quality using an LLM judge during each run when quality repair is enabled.

#### Scenario: Judge executes with candidate pool
- GIVEN a run with at least five non-video candidates
- WHEN quality repair is enabled
- THEN runtime SHALL call the quality judge with current Must-read and candidate pool context
- AND runtime SHALL record judge outputs (score, issues, repaired IDs)

### Requirement: Repair SHALL Trigger Only Below Threshold
The system SHALL apply Must-read rewrite only when `quality_score` is below configured threshold.

#### Scenario: Low quality score triggers rewrite
- GIVEN judge output with `quality_score < threshold`
- WHEN repaired ids are valid and in candidate pool
- THEN runtime SHALL replace Must-read with repaired ids in returned order
- AND runtime SHALL rebuild Skim without duplicates

#### Scenario: High quality score skips rewrite
- GIVEN judge output with `quality_score >= threshold`
- WHEN runtime evaluates repair policy
- THEN runtime SHALL keep original Must-read unchanged

### Requirement: Fail-open Behavior SHALL Be Supported
The system SHALL support fail-open behavior for quality repair failures.

#### Scenario: Judge failure in fail-open mode
- GIVEN quality judge request or schema validation fails
- AND `quality_repair_fail_open = true`
- WHEN runtime handles quality repair
- THEN runtime SHALL continue with baseline Must-read
- AND runtime SHALL log the failure without failing the run

### Requirement: Cross-run Learning SHALL Update Ranking Priors
The system SHALL learn from repair outcomes and explicit feedback signals.

#### Scenario: Repair decision updates priors
- GIVEN a run where repaired Must-read differs from original
- WHEN runtime persists quality outcomes
- THEN runtime SHALL update feature priors for promoted/demoted patterns
- AND subsequent runs SHALL apply decayed bounded offsets from priors
