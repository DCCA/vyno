# Proposal: YouTube Noise Sanitization

## Why
Some YouTube items carry long promotional descriptions and source-link dumps that degrade digest readability.

## Scope
- Add YouTube text sanitization before scoring/summarization.
- Add summary quality validation with fallback.
- Add renderer hard caps and defensive text cleanup.
- Add TDD coverage for noisy-content cases.

## Out of Scope
- Re-ranking policy redesign.
- New source connectors.
