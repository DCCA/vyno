# Proposal: Must-read Source Diversity Cap

## Why
Digest outputs can become dominated by one high-volume source (for example arXiv), reducing practical diversity in Must-read even when other sources are ingested successfully.

## Scope
- Add a configurable per-source cap for Must-read selection.
- Keep full ranking logic intact while rebalancing final Must-read picks.
- Document and test the behavior.

## Out of Scope
- Source ingestion protocol changes.
- New relevance scoring models.
