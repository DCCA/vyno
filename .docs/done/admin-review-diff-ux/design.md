# Design: Admin Review Diff UX

## Approach
- Implement a frontend-only recursive diff helper for immediate local preview.
- Track baseline profile from latest loaded effective profile.
- Keep existing server diff endpoint and button, but improve empty-state messaging.

## UI Changes
- Review tab now has two sections:
  - `Pending Local Diff`: live unsaved changes.
  - `Server Canonical Diff`: result of Compute Diff.
- Add local change count and invalid JSON badge.
- Add alert for JSON parse errors.

## Action Guardrails
- Disable Validate/Compute Diff/Save when JSON payload is invalid.
- Parse editor payload with a shared helper to enforce object payload shape.

## Verification
- TypeScript + Vite production build passes.
- Existing backend/unit regression suite remains green.

