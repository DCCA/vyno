# Design: Timestamped Obsidian Notes Per Run

## Design Goals
- Prevent same-day note overwrites.
- Keep outputs easy to browse by day.
- Preserve deterministic, audit-friendly file naming.

## Path Strategy
Default path strategy (UTC-based):
- Directory: `AI Digest/YYYY-MM-DD/`
- Filename: `HHmmss-<run_id>.md`
- Example: `AI Digest/2026-02-22/134510-a1b2c3d4e5f6.md`

## Metadata Strategy
Add frontmatter fields:
- `date`: `YYYY-MM-DD`
- `generated_at_utc`: full ISO UTC timestamp
- `run_id`: run identifier
- `source_count`: selected candidate count

## Configuration
Add output config option:
- `obsidian_naming`: `timestamped` (default) or `daily`

Behavior:
- `timestamped`: `AI Digest/YYYY-MM-DD/HHmmss-<run_id>.md`
- `daily`: legacy `AI Digest/YYYY-MM-DD.md`

## API/Code Changes
- Update runtime to pass `run_id` and run UTC timestamp into Obsidian writer.
- Update Obsidian writer path builder to branch on naming mode.
- Keep atomic write behavior unchanged.

## Tradeoffs
- Pros: preserves each run, better audit trail, no accidental overwrite.
- Cons: more files per day; user may need a “latest” convenience note later.

## Risks
- Existing user workflows may expect one file per day.
- Mitigation: provide `obsidian_naming: daily` compatibility mode.
