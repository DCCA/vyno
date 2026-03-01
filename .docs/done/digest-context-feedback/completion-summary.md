# Completion Summary: digest-context-feedback

## What changed
- Added contextual run feedback payload to `RunReport` in `src/digest/models.py`.
- Built runtime funnel context snapshot in `src/digest/runtime.py` with fetched, filtered, and selected counts.
- Added sparse-run explanatory note generation for low-item runs.
- Rendered context block in Obsidian notes in `src/digest/delivery/obsidian.py`.
- Rendered compact context block in Telegram messages in `src/digest/delivery/telegram.py`.

## Verification
- `make test` passed (113 tests).
- `make web-ui-build` passed.

## Notes
- Ranking and filtering policies are unchanged; this change is informational only.
