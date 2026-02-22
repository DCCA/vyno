# Completion Summary: Timestamped Obsidian Notes Per Run

## What Changed
- Added configurable Obsidian naming mode: `output.obsidian_naming` (`timestamped` default, `daily` legacy).
- Implemented timestamped note paths in default mode:
  - `AI Digest/YYYY-MM-DD/HHmmss-<run_id>.md`
- Kept legacy behavior behind `daily` mode:
  - `AI Digest/YYYY-MM-DD.md`
- Added run metadata to note frontmatter:
  - `run_id`
  - `generated_at_utc`
- Updated runtime to pass run metadata into Obsidian rendering/writing.
- Updated README with naming mode documentation and examples.

## Verification
- Automated tests:
  - `make test` -> PASS (18 tests)
- Live manual verification:
  - Two same-day live runs succeeded and created distinct note files:
    - `obsidian-vault/AI Digest/2026-02-22/013957-856e0370f981.md`
    - `obsidian-vault/AI Digest/2026-02-22/014010-73554e903ca9.md`

## Risks
- Timestamped mode increases file count per day.
- Users relying on single-file daily behavior must set `obsidian_naming: daily`.

## Follow-ups
- Optional: add `latest.md` convenience pointer per day.
- Optional: add note index file for each day folder.
