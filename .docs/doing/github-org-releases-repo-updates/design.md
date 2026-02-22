# Design: GitHub Org Releases and Repo Updates

## Approach
Extend the existing GitHub connector with an org ingestion branch that normalizes org identifiers and emits only repo-update and release items.

## Config Changes
- `sources.yaml`
  - Add `github_orgs`.
- `profile.yaml`
  - Add GitHub org guardrails:
    - `github_min_stars`
    - `github_include_forks`
    - `github_include_archived`
    - `github_max_repos_per_org`
    - `github_max_items_per_org`

## Ingestion Flow
1. Normalize each org value (`https://github.com/<org>` or `<org>` -> `<org>`).
2. Fetch org repos sorted by recent updates.
3. Apply guardrails and cap repos per org.
4. Emit one `github_repo` item per selected repo.
5. Fetch recent releases per selected repo and emit `github_release` items.
6. Cap total org-derived items per org.

## Compatibility
- Existing repo/topic/query ingestion remains unchanged.
- Org path does not fetch issues/PRs.
- Existing scoring and delivery consume canonical items without changes.

## Risks
- Large orgs can still generate high volume if bounds are too high.
- GitHub API latency/rate limits can reduce org completeness.

## Mitigations
- Default bounded limits and filter knobs.
- Preserve partial-success behavior already present in runtime.
