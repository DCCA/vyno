# Spec

### Requirement: Telegram Minimum Item Count
The Telegram digest renderer SHALL target at least ten rendered items when the selected digest pool contains ten or more items.

#### Scenario: Must-read is shorter than ten
- GIVEN a digest with five `must_read` items and additional selected `skim` items
- WHEN the Telegram digest is rendered
- THEN the renderer SHALL include at least ten total items
- AND the extra items SHALL come from the existing selected pool

#### Scenario: Fewer than ten selected items exist
- GIVEN a digest with fewer than ten selected items total
- WHEN the Telegram digest is rendered
- THEN the renderer SHALL include all available selected items
- AND it SHALL NOT fabricate or fetch new items

### Requirement: Telegram Source Diversity
The Telegram digest renderer SHALL prefer source diversity and avoid one-source digests when the selected pool contains multiple sources.

#### Scenario: Diverse selected pool
- GIVEN a selected pool that contains items from at least five distinct sources
- WHEN the Telegram digest is rendered
- THEN the first-pass item selection SHALL include at least five distinct sources
- AND lower-ranked selected items MAY be promoted over duplicate-source items to achieve that diversity

#### Scenario: Concentrated selected pool
- GIVEN a selected pool that contains fewer than five distinct sources
- WHEN the Telegram digest is rendered
- THEN the renderer SHALL use the best available mix from that pool
- AND it SHALL preserve the existing selected pool boundaries

### Requirement: Scope Isolation
The change SHALL be isolated to Telegram rendering.

#### Scenario: Other outputs remain stable
- GIVEN the updated Telegram renderer
- WHEN Obsidian notes and runtime selection counts are produced
- THEN their existing limits and behavior SHALL remain unchanged
