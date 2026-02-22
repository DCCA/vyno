# Spec: GitHub Org Releases and Repo Updates

### Requirement: GitHub Org Source Configuration
The system SHALL support `github_orgs` in `sources.yaml`.

#### Scenario: Org URL accepted
- GIVEN `github_orgs: ["https://github.com/vercel-labs"]`
- WHEN source config loads
- THEN the org identifier is normalized to `vercel-labs`

#### Scenario: Org login accepted
- GIVEN `github_orgs: ["vercel-labs"]`
- WHEN source config loads
- THEN the org identifier remains `vercel-labs`

### Requirement: Org Ingestion Type Restriction
The system SHALL ingest only repository updates and releases from `github_orgs`.

#### Scenario: Org ingestion output types
- GIVEN one configured org
- WHEN GitHub ingestion executes
- THEN output contains only `github_repo` and `github_release` items from that org
- AND output does not contain `github_issue` or `github_pr` items from org ingestion

### Requirement: Org Quality Guardrails
The system SHALL apply configurable org repository filters before item emission.

#### Scenario: Repo excluded by filters
- GIVEN a repo that is archived or below minimum stars
- WHEN org repos are evaluated
- THEN that repo is excluded from org-derived digest items

### Requirement: Bounded Org Ingestion
The system SHALL bound org ingestion to protect runtime and ranking quality.

#### Scenario: Large organization
- GIVEN an org with many repositories
- WHEN org ingestion executes
- THEN processed repositories are limited by `github_max_repos_per_org`
- AND org-derived emitted items are limited by `github_max_items_per_org`

### Requirement: Backward Compatibility
The system SHALL preserve existing `github_repos`, `github_topics`, and `github_search_queries` behavior.

#### Scenario: Existing configuration without orgs
- GIVEN a configuration that does not define `github_orgs`
- WHEN the digest runs
- THEN GitHub ingestion behavior remains unchanged from prior implementation
