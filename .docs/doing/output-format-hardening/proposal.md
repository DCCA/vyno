# Proposal: Output Format Hardening

## Why
Digest content quality is constrained by output formatting. Obsidian notes should be easier to browse and query, and Telegram delivery should be resilient to long content while staying readable.

## Scope
- Refine Obsidian renderer to follow consistent frontmatter and markdown structure.
- Refine Telegram renderer for compact sections and safe chunking under message limits.
- Keep runtime and delivery behavior backward-compatible.

## Out of Scope
- New delivery channels.
- Ranking policy changes.
