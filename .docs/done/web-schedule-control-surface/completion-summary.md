# Web Schedule Control Surface

Added a dedicated `Schedule` workspace so daily automation can be managed directly from the web product instead of being edited only inside onboarding/profile fields.

## What changed
- Added a new `Schedule` route and ready-state nav item for recurring users.
- Added a dedicated `SchedulePage` with:
  - automation status
  - schedule controls
  - plain-language next-run preview
  - issue/recovery guidance
- Added a separate schedule draft/save flow backed by the existing schedule endpoints.
- Reworked onboarding and profile so they now link into schedule controls instead of duplicating the full schedule editor.
- Added the HTML wireframe artifact at `.docs/tmp/schedule-control-wireframe.html`.

## Verification
- `npm --prefix web run test`
- `npm --prefix web run build`
- Browser sanity check at `/schedule` on a live local app

## Notes
- This remains a single daily schedule surface.
- No backend scheduler model changes were required.
