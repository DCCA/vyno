# Proposal: Timestamped Obsidian Notes Per Run

## Why
Current Obsidian output uses one file per date, which can overwrite prior content when users run the digest multiple times in the same day.

## Current State
- Notes are written to `AI Digest/YYYY-MM-DD.md`.
- Multiple runs on the same day target the same file path.

## Scope
- Introduce timestamped note naming so each run writes a unique file.
- Keep notes grouped by day for discoverability.
- Preserve run metadata in frontmatter for auditability.

## Out of Scope
- Changes to ingestion, scoring, or ranking logic.
- Changes to Telegram delivery behavior.

## Success Conditions
- Two runs on the same day produce two distinct Obsidian files.
- No run overwrites a previous note by default.
- Generated paths are deterministic and filesystem-safe.
