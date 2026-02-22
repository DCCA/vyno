# Completion Summary: X Posts and GitHub Ingestion

## What Changed
- Added X manual inbox connector: `src/digest/connectors/x_inbox.py`.
- Added GitHub API connector: `src/digest/connectors/github.py`.
- Extended source config with:
  - `x_inbox_path`
  - `github_repos`
  - `github_topics`
  - `github_search_queries`
- Extended profile config with:
  - `trusted_authors_x`, `blocked_authors_x`
  - `trusted_orgs_github`, `blocked_orgs_github`
- Added new item types:
  - `x_post`, `github_release`, `github_issue`, `github_pr`, `github_repo`
- Integrated X/GitHub fetch stages into runtime with structured logs.
- Updated rule scoring to support trusted/blocked X authors and GitHub orgs.
- Updated sample configs and README guidance.

## Verification
- Automated tests: `make test` -> PASS (26 tests)
- Live run: `make live` -> PASS (`run_id=0b33edeb4fbd`, `status=success`)
- Log evidence confirms source ingestion stages:
  - `fetch_x_inbox` (item_count tracked)
  - `fetch_github` (item_count tracked)

## Risks
- X inbox quality depends on manual link curation.
- GitHub API rate limits may reduce item volume without token.

## Follow-ups
- Add score caching for GitHub/X items to reduce repeated agent calls.
- Add richer X metadata extraction beyond URL+inbox context.
