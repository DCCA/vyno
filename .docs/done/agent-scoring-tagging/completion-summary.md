# Completion Summary: Agent Scoring and Tagging

## What Changed
- Added agent-based scorer/tagger using OpenAI Responses API (`src/digest/scorers/agent.py`).
- Added fallback behavior to rules-based scoring per item when agent scorer fails.
- Added `agent_scoring_enabled` config flag in profile (default `true`).
- Extended score model with:
  - `tags`
  - `topic_tags`
  - `format_tags`
  - `provider`
- Extended SQLite `scores` storage with metadata columns:
  - `tags_json`
  - `topic_tags_json`
  - `format_tags_json`
  - `provider`
- Updated Obsidian rendering to include tags per item.

## Verification
- `make test` -> PASS (22 tests)
- Live run -> PASS (`run_id=6510b184b15b`, `status=success`)
- DB validation confirms persisted providers/tags for latest run.

## Risks
- Agent scoring increases runtime due per-item API calls.
- API failures still possible; rules fallback mitigates availability risk.

## Follow-ups
- Add top-N prefilter before agent calls to reduce cost/latency.
- Add prompt caching and score caching by item hash.
