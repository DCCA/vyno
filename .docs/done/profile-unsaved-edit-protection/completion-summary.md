# Completion Summary: profile-unsaved-edit-protection

## Delivered
- Updated `web/src/App.tsx` so background polling no longer overwrites unsaved `runPolicy` edits on the Profile screen.
- Updated full refresh hydration so dirty profile workspace state is preserved during ordinary refreshes.
- Forced canonical server rehydration only after successful save/apply flows so pending state clears correctly once persistence completes.
- Added frontend source coverage for the dirty-state guards and revalidated the browser save flow on the local Profile UI.

## Verification
- `npm --prefix web run test` passed.
- `npm --prefix web run build` passed.
- Browser validation confirmed that changing digest mode to `Catch up` survives the 8-second poll interval and saves correctly.

## Notes
- The browser validation changed local runtime state through the UI, but only in ignored overlay/runtime files.
- This fix preserves operational polling for status/health while protecting unsaved profile workspace edits.
