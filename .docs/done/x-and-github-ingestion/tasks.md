# Tasks: X Posts and GitHub Ingestion

- [x] 1.1 Extend `sources.yaml` schema for X inbox + GitHub selectors.
- [x] 1.2 Extend `profile.yaml` schema for trusted/blocked X/GitHub identities.
- [x] 1.3 Add env token handling for GitHub API auth.

- [x] 2.1 Implement `connectors/x_inbox.py` for manual X link ingestion.
- [x] 2.2 Implement link parsing/validation and canonicalization for X links.
- [x] 2.3 Add connector-level error handling and logging.

- [x] 3.1 Implement `connectors/github.py` for repos/topics/search ingestion.
- [x] 3.2 Map releases/issues/PRs/repos into canonical `Item` schema.
- [x] 3.3 Add API pagination/rate-limit handling with retries/backoff.

- [x] 4.1 Add new item types to models and ensure downstream compatibility.
- [x] 4.2 Integrate X/GitHub connectors into runtime source fetch flow.
- [x] 4.3 Ensure dedupe/scoring/selection handles new item types.

- [x] 5.1 Update scoring rules for trusted/blocked X/GitHub entities.
- [x] 5.2 Ensure agent scorer prompt handles new item types.
- [x] 5.3 Verify tag output quality for GitHub and X content.

- [x] 6.1 Update Telegram and Obsidian rendering for new source types.
- [x] 6.2 Verify link formatting and tags display in outputs.

- [x] 7.1 Add unit tests for X inbox parsing and GitHub response mapping.
- [x] 7.2 Add integration fixture test for mixed-source run.
- [x] 7.3 Add failure-path tests (bad links, API errors, partial source outage).

- [x] 8.1 Update README with configuration and token setup.
- [x] 8.2 Run full test suite and live validation.
- [x] 8.3 Write completion summary and move folder to `.docs/done/`.
