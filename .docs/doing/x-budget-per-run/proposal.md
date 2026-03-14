# Proposal: X Budget Per Run

## Why
- X selector reads now have a known direct cost per post.
- Operators want a hard per-run spend ceiling rather than a loose per-selector item cap.
- The current `DIGEST_X_MAX_ITEMS_PER_SELECTOR` control cannot enforce a dollar budget across all X selectors in one run.

## Scope
- Add profile-level X spend controls.
- Derive a hard per-run X post budget from cost and spend.
- Allocate that budget before X selector fetches begin.
- Surface the budget in the operator profile controls.

## Non-Goals
- Dynamic cost estimation from X billing APIs.
- Pagination changes or multi-page selector fetching.
- Budgeting local `x_inbox` processing.
