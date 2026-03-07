# Completion Summary: github-owner-fallback

## Delivered
- Updated `src/digest/connectors/github.py` so `github_org` ingestion first tries `/orgs/{login}/repos` and falls back to `/users/{login}/repos` when GitHub returns `404`.
- Preserved the existing repo filtering, repo item mapping, and release fetching logic after the fallback.
- Updated `src/digest/ops/source_registry.py` and `README.md` so `github_org` is documented and validated as a GitHub owner selector, not org-only.
- Added regression coverage in `tests/test_github_connector.py` for user-owner fallback.

## Verification
- `python3 -m unittest tests.test_github_connector tests.test_source_registry -v` passed.
- `make test` passed (`156` tests).

## Notes
- The public config shape remains unchanged: `github_orgs` still holds owner logins/URLs for backward compatibility.
- Non-`404` GitHub API errors still fail normally and are not masked by the fallback.
