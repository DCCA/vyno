# Completion Summary: Admin Filter Visibility

## What Changed
- Added run-level filter telemetry for admin visibility:
  - dedupe dropped counts (including videos)
  - window dropped counts
  - seen dropped/re-added counts
  - blocked dropped counts
  - low-impact GitHub issue drops
  - ranking dropped counts
- Added a video funnel across stages:
  - fetched -> post-window -> post-seen -> post-block -> selected
- Rendered filter and video funnel context lines in both Telegram and Obsidian outputs.
- Updated runtime integration and renderer tests to validate the new context data.

## Verification
- Executed full test suite with `make test`.
- Result: all tests passed.

## Risks / Follow-Ups
- Current telemetry is aggregate-only per run; it does not list per-item rejection reasons.
- Follow-up option: add an admin-only "top dropped items by stage" diagnostic view.

