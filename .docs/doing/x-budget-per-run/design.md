# Design: X Budget Per Run

## Config
- Add `x_cost_per_post_usd` and `x_max_spend_per_run_usd` to `ProfileConfig`.
- Validate them during profile parsing.

## Runtime
- Compute `x_posts_budget_per_run = floor(max_spend / cost_per_post)`.
- Build per-selector limits before X fetch:
  - split evenly across `x_author` selectors when authors exist
  - allocate `0` to themes when authors are configured
  - otherwise split evenly across themes
- Pass per-selector limits into `x_selectors` so zero-budget selectors are skipped.

## UI
- Add two numeric controls in the Profile quality/cost section.
- Show a derived “max posts per run” explanation line.
