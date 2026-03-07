# Completion Summary: Review Route Removal

## Outcome
- Removed the standalone `Review` workspace from the web console.
- Consolidated advanced diff inspection into `Profile` expert mode via the new `Diff tools` tab.
- Simplified navigation, route typing, and local notice scope so `Review` is no longer treated as a first-class surface.

## Affected Paths
- `web/src/App.tsx`
- `web/src/app/navigation.ts`
- `web/src/app/types.ts`
- `web/src/lib/console-utils.ts`
- `web/src/features/profile/ProfilePage.tsx`
- `web/tests/digest-policy-ui.test.mjs`
- `web/tests/ui-feedback-locality.test.mjs`
- `web/tests/ui-redesign-layout.test.mjs`

## Verification
- `npm --prefix web run test`
- `npm --prefix web run build`
- Local browser validation on `http://127.0.0.1:4174/profile` confirmed:
  - no `Review` navigation item
  - `Profile` remains reachable
  - advanced diff guidance now points to `Expert mode` inside `Profile`
