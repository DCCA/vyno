# Proposal

## Why
The local digest source overlay needs additional high-signal AI, LLM, and coding-agent sources so the digest captures more relevant builder and research updates without changing the tracked base defaults.

## Scope
- Add validated RSS feeds for AI, LLM, and agent-building coverage to `data/sources.local.yaml`.
- Add validated YouTube channel IDs for coding and AI-agent creators to `data/sources.local.yaml`.
- Avoid introducing duplicates against the effective merged source set.
- Verify the merged config loads and the added public feeds respond.

## Non-Goals
- Rework tracked defaults in `config/sources.yaml`.
- Change any runtime source-fetching behavior.
- Add X or GitHub selectors in this change.
