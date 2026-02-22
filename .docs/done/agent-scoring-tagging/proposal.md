# Proposal: Agent Scoring and Tagging

## Why
Rules-only scoring is deterministic but limited. We need richer scoring and structured tagging to improve ranking quality and downstream organization in Obsidian.

## Scope
- Add LLM agent scoring via OpenAI Responses API.
- Add per-item tags (`tags`, `topic_tags`, `format_tags`).
- Persist score tags/provider metadata in SQLite.
- Keep rules-based scoring as fallback when agent scoring fails.

## Out of Scope
- Personalized learning loops and A/B experimentation framework.
- New delivery channels beyond existing Telegram + Obsidian outputs.

## Success Conditions
- Agent scoring runs when enabled and credentials are available.
- Fallback rules scoring preserves run reliability on agent failures.
- Obsidian notes include tags for organization.
