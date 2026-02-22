# Proposal: GitHub Org Releases and Repo Updates

## Why
Users want to register an org like `https://github.com/vercel-labs` and receive daily digest updates without manual per-repo curation.

## Scope
- Add `github_orgs` source support with URL/login normalization.
- Ingest org updates as:
  - `github_repo` (repo updated activity)
  - `github_release` (recent releases)
- Add org guardrails and ingestion bounds.
- Keep existing GitHub source modes (`repos`, `topics`, `search_queries`) intact.

## Out of Scope
- Org issues and PR ingestion from `github_orgs`.
- New delivery channels or ranking model redesign.

## Success Conditions
- `github_orgs` accepts org URL and login forms.
- Daily runs include org repo/release items only.
- Org ingestion stays bounded and lower-noise via configurable filters.
