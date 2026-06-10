# Project Status And Setup Polish Proposal

## Why

The quality gates are now repaired, but the public README still reports older verification counts and does not clearly distinguish first-run setup from later `make doctor` checks. This makes the project harder to resume and understand from GitHub.

## Scope

- Refresh the README status snapshot and verification counts.
- Clarify the first-run, zero-key setup path.
- Document that production dependency audit is clean while the remaining full-audit item is dev-server-only and intentionally deferred.
- Update GitHub repository description and topics outside the PR because those are repository settings rather than files.

## Non-goals

- No runtime behavior changes.
- No dependency upgrades.
- No UI changes.
- No large module refactors.
