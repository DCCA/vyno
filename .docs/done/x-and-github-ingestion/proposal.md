# Proposal: X Posts and GitHub Ingestion

## Why
High-signal AI content increasingly appears on X and GitHub before traditional news sources. Current ingestion misses many timely releases, demos, and technical discussions.

## Scope
- Add X content ingestion via manual link inbox (MVP-safe path).
- Add GitHub ingestion via official API for releases/issues/PRs/repos.
- Normalize X/GitHub items into existing digest pipeline.
- Reuse existing scoring/tagging and delivery outputs.

## Out of Scope
- Fully automated X API ingestion in MVP.
- Personalization loops and ranking model retraining.

## Success Conditions
- Digest can include X and GitHub items in same run.
- Source failures remain isolated (partial runs still deliver).
- New item types are scored/tagged and appear in Obsidian/Telegram outputs.
