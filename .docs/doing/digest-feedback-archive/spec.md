# Spec: Digest Feedback Archive

### Requirement: Digest-Wide Source Diversity
The system SHALL reduce repeated sources across the full non-video digest, not only within `must_read`.

#### Scenario: Same-source items dominate ranking
- GIVEN many top-ranked non-video items from the same source family
- WHEN the digest sections are selected
- THEN the final `must_read + skim` selection SHALL apply a conservative same-source cap
- AND the digest SHALL still use a fallback pass so strong digests do not become artificially sparse

### Requirement: Content Depth Preference
The system SHALL support a profile-level content depth preference that adjusts ranking for technical items.

#### Scenario: Practical preference suppresses dense items
- GIVEN a profile with `content_depth_preference` set to `practical`
- WHEN a highly technical item is scored
- THEN the runtime SHALL apply a negative ranking adjustment
- AND the item MAY still appear if its overall score remains strong enough

#### Scenario: Invalid preference is configured
- GIVEN a profile payload with an unsupported depth preference
- WHEN the profile is loaded
- THEN configuration validation SHALL reject the payload

### Requirement: Delivered Digest Archive
The system SHALL persist exact delivered artifacts and selected items for each non-preview run.

#### Scenario: Run finishes successfully
- GIVEN a non-preview run that completes
- WHEN delivery artifacts are produced
- THEN the system SHALL archive the final Telegram payload and rendered Obsidian note
- AND the system SHALL persist the selected items for that run
- AND the archive SHALL be retrievable by run id

#### Scenario: Container is recreated
- GIVEN an archived run created in Docker
- WHEN the container is recreated
- THEN the archive SHALL remain retrievable from mounted persistent storage or SQLite metadata

### Requirement: Feedback Capture And Learning
The system SHALL capture explicit feedback on delivered items and sources and make it available to future ranking.

#### Scenario: Item feedback is submitted
- GIVEN an archived run item in Timeline review
- WHEN the operator submits `too_technical` or `repeat_source`
- THEN the system SHALL store the feedback event with derived ranking features
- AND future ranking SHALL be able to use those features as bias inputs

#### Scenario: Source mute is submitted
- GIVEN a source entry in the Sources workspace
- WHEN the operator submits `mute_source`
- THEN the system SHALL record the feedback event
- AND the system SHALL add that source to the appropriate blocked-source preference bucket

### Requirement: Existing Console Surfaces Remain The Review Path
The system SHALL expose archive review and feedback through existing console surfaces.

#### Scenario: Reviewing a prior run
- GIVEN a run is selected in Timeline
- WHEN archived artifacts and run items exist
- THEN the Timeline surface SHALL show the archived digest payloads and item-level feedback controls
- AND the Profile surface SHALL expose the content depth preference and feedback summary
- AND the Sources surface SHALL expose source-level preference actions
