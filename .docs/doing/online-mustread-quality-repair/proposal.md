# Proposal: Online Must-read Quality Repair

## Why
Must-read output can be topically relevant but still low utility (high redundancy, weak source diversity, generic summaries). We need an online mechanism that judges each run and repairs Must-read before delivery.

## Scope
- Add an LLM quality judge step in runtime for Must-read.
- Trigger full Must-read rewrite when `quality_score < threshold`.
- Keep repair constrained to a candidate pool from ranked items.
- Persist quality eval records and cross-run priors.
- Apply priors as bounded ranking offsets in subsequent runs.

## Out of Scope
- Changing upstream connectors or source coverage.
- Replacing core scoring model.
- Building a standalone dashboard for quality analytics in this change.
