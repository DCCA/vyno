# Spec: source-identity-cards

### Requirement: Latest-Item Source Preview Cards
The Sources workspace SHALL render each configured source as a preview card based on the latest stored item linked to that source.

#### Scenario: RSS preview card
- GIVEN a configured RSS source with a stored fetched item
- WHEN the operator opens the Sources workspace
- THEN the card shows preview title, summary, host, and optional image for the latest linked item
- AND the source identity remains visible on the same card

#### Scenario: Source without stored items
- GIVEN a configured source with no linked stored items yet
- WHEN the operator opens the Sources workspace
- THEN the card renders a non-image fallback state
- AND the card explains that a digest run is needed to populate the preview

### Requirement: Source-Linkage Integrity
The system SHALL persist an explicit mapping between configured sources and stored items.

#### Scenario: Shared item URLs across multiple sources
- GIVEN the same item is fetched from more than one configured source
- WHEN the runtime stores the item and source links
- THEN each source retains its own linkage to that item
- AND latest-item lookup for one source SHALL NOT depend on heuristic source-string parsing

### Requirement: Safe Handling For Config-Only Entries
The Sources workspace SHALL not offer unsupported mutation actions for sources that are visible but not managed by the source editor.

#### Scenario: X inbox utility card
- GIVEN the API includes an `x_inbox` entry in the sources payload
- WHEN the operator views the source library
- THEN the entry renders as a config-oriented fallback card
- AND edit/delete controls are not shown for that card
