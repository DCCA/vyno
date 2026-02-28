# Spec: Must-read Source Diversity Cap

### Requirement: Must-read Selection SHALL Limit Per-source Dominance
The system SHALL cap Must-read items from the same source family/domain using `must_read_max_per_source`.

#### Scenario: One source dominates ranked candidates
- GIVEN top-ranked non-video items are mostly from one source
- WHEN Must-read selection runs
- THEN selection SHALL include at most `must_read_max_per_source` items from that source
- AND remaining Must-read slots SHALL be filled from other ranked sources when available

#### Scenario: Not enough alternative sources
- GIVEN alternative sources are insufficient
- WHEN Must-read cap filtering reduces candidates
- THEN selection SHALL backfill from remaining ranked items to preserve Must-read count
