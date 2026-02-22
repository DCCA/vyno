# Design: Agent Scoring and Tagging

## Approach
Add a dedicated Responses API scorer component that outputs structured scores and tags. Keep the existing rule scorer as a per-item fallback for reliability.

## Scoring Contract
Agent JSON output fields:
- `relevance` (0-10)
- `quality` (0-10)
- `novelty` (0-10)
- `total` (0-30)
- `tags` (max 5)
- `topic_tags` (controlled vocabulary)
- `format_tags` (controlled vocabulary)
- `reason` (short text)

To preserve ranking compatibility, agent sub-scores are mapped to existing weighted ranges:
- relevance * 6
- quality * 3
- novelty * 1

## Data Model Updates
`scores` table extensions:
- `tags_json`
- `topic_tags_json`
- `format_tags_json`
- `provider`

## Configuration
`profile.yaml` adds:
- `agent_scoring_enabled: true|false` (default true)

## Reliability
- If scorer init fails, use rules scorer for all items.
- If scorer fails per item, fallback to rules scorer only for that item.
- Log fallback events with run_id and item_id.
