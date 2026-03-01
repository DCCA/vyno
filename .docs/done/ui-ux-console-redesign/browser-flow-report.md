# Browser Flow Report: ui-ux-console-redesign

Date: 2026-03-01

## Environment
- API: `make web-api` on `http://127.0.0.1:8787`
- UI: `npm --prefix web run dev -- --host 127.0.0.1 --port 5173`
- Browser automation: `npx -y agent-browser --session-name vyno-ui`

## Flows Executed
1. Opened redesigned UI and switched modes (Setup Journey <-> Manage Workspace).
2. Setup Journey:
   - Ran preflight.
   - Applied source pack.
   - Triggered preview.
3. Manage Workspace:
   - Added source (`https://example.com/feed.xml`).
   - Removed source (`https://example.com/feed.xml`).
   - Ran Review actions (Validate, Compute Diff, Save Overlay).
   - Ran History rollback action.
4. Triggered `Run now` from header and verified live progress card updates.

## Result
- No UI transport regressions observed (`TypeError: Failed to fetch` did not occur).
- API request logs show successful 200 responses for exercised web endpoints.
- Setup-first and manage-mode navigation remained operable throughout actions.

## Evidence
- Screenshot captured by agent-browser:
  - `/run/user/1000/agent-browser/tmp/screenshots/screenshot-2026-03-01T01-08-33-444Z-90o7ee.png`
