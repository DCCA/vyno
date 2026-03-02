# Completion Summary: Source Grid Status Hover Clarity

## Delivered
- Desktop Sources table simplified to `Type`, `Source`, `Status`, and `Actions`.
- Diagnostics moved to status hover/focus detail (`title`) per row.
- `Edit` and `Delete` controls remain visible in-row.
- Existing filtering, status filtering, and show-more behavior preserved.
- UI source-density test expectations updated.

## Verification
- `npm --prefix web run test` passed.
- `npm --prefix web run build` passed.
