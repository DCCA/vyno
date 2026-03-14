# Spec: Final Digest Source Diversity

### Requirement: Final Digest Source Cap Preservation
The system SHALL preserve the configured source-diversity caps after quality repair rebuilds the digest.

#### Scenario: Repair changes Must-read
- GIVEN a repaired Must-read list is accepted
- WHEN the final digest sections are rebuilt
- THEN the system SHALL recompute skim under the digest-wide source cap
- AND the final non-video digest SHALL not exceed the configured per-source limit

### Requirement: Invalid Repair Fallback
The system SHALL reject repaired Must-read outputs that violate source-diversity constraints.

#### Scenario: Repair over-concentrates one source
- GIVEN the quality-repair model returns a Must-read list with too many items from the same source family
- WHEN the repair result is validated
- THEN the system SHALL reject the repair result
- AND the run SHALL continue with the pre-repair digest sections

### Requirement: Balanced Research Concentration
The system SHALL apply a bounded penalty when research-heavy sources dominate the top candidate pool.

#### Scenario: Paper-heavy ranking
- GIVEN the highest-ranked non-video candidates are dominated by research-paper items from the same paper-oriented source family
- WHEN ranking adjustments are applied
- THEN the system SHALL reduce those items' ranking modestly
- AND exceptional research items MAY still remain in the final digest

### Requirement: Diversity Visibility
The system SHALL expose final source-family concentration in run diagnostics.

#### Scenario: Delivered digest inspection
- GIVEN a digest run completes
- WHEN the run context and timeline are recorded
- THEN the system SHALL include source-family counts for the delivered digest
- AND repair rejection or fallback reasons SHALL be logged when triggered
