# Spec: Timestamped Obsidian Notes Per Run

### Requirement: Unique Note Per Run
The system SHALL write a unique Obsidian note file for every digest run.

#### Scenario: Two manual runs on same day
- GIVEN two successful manual runs executed on the same UTC date
- WHEN Obsidian notes are written
- THEN the resulting file paths are different
- AND no existing file is overwritten

### Requirement: Timestamped Naming Convention
The system SHALL use timestamped naming in Obsidian output paths.

#### Scenario: Timestamped path structure
- GIVEN a run with UTC timestamp `2026-02-22T13:45:10Z`
- WHEN note path is generated
- THEN path follows `AI Digest/2026-02-22/134510-<run_id>.md`

### Requirement: Daily Grouping
The system SHALL group timestamped notes under a per-day directory.

#### Scenario: Same-day grouping
- GIVEN multiple runs on `2026-02-22`
- WHEN notes are written
- THEN all note files are stored under `AI Digest/2026-02-22/`

### Requirement: UTC Consistency
The system SHALL derive note date and time from the run UTC timestamp.

#### Scenario: Midnight boundary
- GIVEN one run at `2026-02-22T23:59:59Z` and another at `2026-02-23T00:00:01Z`
- WHEN note paths are generated
- THEN notes are written to different date folders (`2026-02-22` and `2026-02-23`)

### Requirement: Frontmatter Run Metadata
The system SHALL include run-level metadata in Obsidian note frontmatter.

#### Scenario: Metadata present
- GIVEN any written note
- WHEN frontmatter is read
- THEN it includes `run_id`
- AND it includes `generated_at_utc`

### Requirement: Backward Compatibility Control
The system SHOULD support a configurable naming mode for transition periods.

#### Scenario: Explicit legacy mode
- GIVEN configuration sets `obsidian_naming: daily`
- WHEN note path is generated
- THEN path follows legacy `AI Digest/YYYY-MM-DD.md`
