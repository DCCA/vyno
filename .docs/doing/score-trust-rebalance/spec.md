# Spec

### Requirement: Soft Source Preference
The system SHALL treat explicit trust inputs as bounded ranking priors rather than raw quality boosts.

#### Scenario: Trusted source item with weak content
- GIVEN an item from a configured preferred source
- WHEN its content quality is below the ranking threshold
- THEN the source preference SHALL NOT increase its final rank

#### Scenario: Strong item from preferred source
- GIVEN an item from a configured preferred source
- WHEN its content quality clears the threshold
- THEN the system MAY apply a small bounded ranking prior
- AND the prior SHALL NOT bypass diversity protections

### Requirement: User-Facing Final Score
The system SHALL show the final adjusted score in user-facing digest review and delivery surfaces.

#### Scenario: Telegram score
- GIVEN a selected digest item
- WHEN the Telegram digest is rendered
- THEN the displayed score SHALL reflect the adjusted final score

#### Scenario: Timeline review score
- GIVEN a selected digest item archived for a run
- WHEN Timeline review is opened
- THEN the displayed score SHALL reflect the adjusted final score
- AND the raw score SHALL remain available for operator inspection

### Requirement: Operator Explanation
The system SHALL preserve score adjustment context for selected items.

#### Scenario: Selected item review
- GIVEN a run item selected into the digest
- WHEN the item is archived
- THEN the system SHALL store raw score, adjusted score, and adjustment breakdown

### Requirement: Clear Preference Wording
The operator console SHALL describe trusted inputs as soft preferences.

#### Scenario: Profile guidance
- GIVEN the profile focus settings
- WHEN the operator reviews source preference controls
- THEN the copy SHALL describe them as preferred reliable inputs, not absolute trust
