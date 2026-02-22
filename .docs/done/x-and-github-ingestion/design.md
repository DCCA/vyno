# Design: X Posts and GitHub Ingestion

## Design Goals
- Add new sources with minimal pipeline disruption.
- Keep MVP reliability high with safe and explicit X ingestion path.
- Preserve existing scoring/delivery interfaces.

## Source Strategy
### X (MVP)
- Ingest from manual inbox (`x_inbox_path`) containing links.
- Parse links, dedupe, and fetch lightweight metadata/content.
- Avoid direct X API dependency in MVP.

### GitHub
- Use GitHub REST API with token auth (`GITHUB_TOKEN`).
- Ingest from:
  - configured repositories (`github_repos`)
  - topic selectors (`github_topics`)
  - search queries (`github_search_queries`)
- Source types:
  - release
  - issue
  - pull request
  - repository update

## Config Additions
### `sources.yaml`
- `x_inbox_path`
- `github_repos`
- `github_topics`
- `github_search_queries`

### `profile.yaml`
- `trusted_authors_x`
- `blocked_authors_x`
- `trusted_orgs_github`
- `blocked_orgs_github`

## Connector Boundaries
- `connectors/x_inbox.py`
- `connectors/github.py`

Each connector returns canonical `Item` objects and handles its own retries/errors.

## Normalization and Item Types
Add item type values:
- `x_post`
- `github_release`
- `github_issue`
- `github_pr`
- `github_repo`

## Reliability
- Source failures are isolated per connector/endpoints.
- Partial success is acceptable and logged.
- No secrets in logs.

## Tradeoffs
- X manual inbox is lower automation but avoids API risk and complexity.
- GitHub API integration adds auth/rate-limit handling but gives strong technical signal.
