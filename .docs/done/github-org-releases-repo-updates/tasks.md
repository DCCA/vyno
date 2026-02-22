# Tasks: GitHub Org Releases and Repo Updates

- [x] 1.1 Add Firehose change artifacts (`proposal.md`, `spec.md`, `design.md`, `tasks.md`).

- [x] 2.1 Add `github_orgs` to source config model and loader.
- [x] 2.2 Add org normalization support for URL/login forms.
- [x] 2.3 Add profile guardrail config for org ingestion quality and bounds.

- [x] 3.1 Extend GitHub connector to ingest org repos as `github_repo` items.
- [x] 3.2 Extend GitHub connector to ingest org releases as `github_release` items.
- [x] 3.3 Ensure org ingestion excludes issues/PRs.

- [x] 4.1 Wire `github_orgs` and guardrail options through runtime GitHub fetch stage.
- [x] 4.2 Keep stage logging and partial-failure behavior intact.

- [x] 5.1 Add/update tests for source loading and org normalization behavior.
- [x] 5.2 Add/update connector tests for org type restriction and mapping.
- [x] 5.3 Add runtime test that verifies org source wiring.

- [x] 6.1 Update sample `sources.yaml` and README docs.
- [x] 6.2 Run full test suite (`make test`).
