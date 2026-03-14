# Design

## Approach
- Keep raw scoring behavior intact except removing direct trust boosts from rule scoring.
- Apply explicit trust inputs in runtime re-ranking as a single bounded source-preference prior.
- Annotate each `Score` with `raw_total`, `adjusted_total`, and `adjustment_breakdown`.
- Persist adjusted score data in `run_selected_items` while keeping backward compatibility for older runs.

## Synthetic User Review
- 10 synthetic users reviewed the mental model of current vs proposed scoring.
- Main finding: users misread `trusted sources` as a promise that those sources should win.
- Improvement chosen:
  - rename the profile wording
  - show final adjusted score in Telegram and Timeline
  - keep explanation detail in Timeline, not in Telegram

## Defaults
- bounded source-preference prior: `+2`
- source preference applies only when the item already meets a minimum quality floor
- tracked defaults remove `arxiv.org` from preferred sources
