# Spec: X Linked Articles Discovery

### Requirement: Trusted X Authors Promote Linked Articles
The system SHALL promote outbound article links from configured `x_author` posts into digest candidates.

#### Scenario: Trusted author shares an article
- GIVEN a configured `x_author` selector returns an X post with a non-X outbound URL
- WHEN selector items are converted into digest items
- THEN the system SHALL keep the original `x_post`
- AND the system SHALL create a promoted linked-article candidate for the outbound URL

### Requirement: Theme Searches Stay Post-Only In V1
The system SHALL keep `x_theme` discovery limited to `x_post` items in v1.

#### Scenario: Theme result contains outbound links
- GIVEN a configured `x_theme` selector returns an X post with outbound URLs
- WHEN selector items are converted into digest items
- THEN the system SHALL keep the `x_post`
- AND the system SHALL NOT create promoted linked-article candidates from that theme result

### Requirement: Duplicate URLs Merge Discovery Context
The system SHALL merge duplicate URLs so X discovery context strengthens the article rather than creating duplicate digest items.

#### Scenario: RSS and X point to the same article
- GIVEN an RSS item and a promoted X-linked article share the same canonical URL
- WHEN deduplication runs
- THEN the system SHALL keep one item for that URL
- AND the merged item SHALL retain the X endorsement context for scoring

### Requirement: X Endorsements Improve Ranking
The system SHALL use trusted X endorsements as a ranking signal for promoted articles.

#### Scenario: Multiple trusted authors share the same article
- GIVEN a merged article contains endorsements from multiple trusted X authors
- WHEN the item is scored
- THEN the system SHALL give that article a higher quality score than the same article without endorsements
- AND the item SHALL expose an `x-discovered` format tag
