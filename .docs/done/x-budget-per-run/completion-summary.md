# Completion Summary

Added a hard per-run X spend cap so selector-based discovery stays within a configured dollar budget.

## What Changed
- Added per-post X cost and max-spend-per-run profile controls.
- Derived a hard post budget per run and allocated it author-first across selectors.
- Exposed the budget in Profile and skipped zero-budget selectors cleanly.

## Verification
- `make test`
- `npm --prefix web run test`
- `npm --prefix web run build`
- Live X API check confirming the enforced budget

## Risks / Follow-Ups
- Author-first allocation means themes receive no budget when authors consume the full cap.
