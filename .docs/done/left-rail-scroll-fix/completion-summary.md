# Left Rail Scroll Fix

Made the desktop left rail internally scrollable while simplifying the rail content so lower navigation stays reachable without extra mode chrome.

## What changed
- Moved sticky positioning to the desktop `aside` container.
- Added a desktop viewport-bound max height and `overflow-y-auto` to the rail container.
- Added stable scrollbar gutter / right padding so rail content does not crowd the scrollbar.
- Removed the separate `Workspace mode` card from the left rail to reduce visual noise.
- Kept schedule state visible by folding it into the existing `System pulse` block.
- Added frontend source-shape coverage for the desktop rail overflow classes.

## Verification
- `npm --prefix web run test`
- `npm --prefix web run build`
- Browser sanity check on the live shell

## Notes
- The change is desktop-focused.
- Mobile menu behavior remains unchanged.
