# Browser Flow Report

## Environment
- API: `make web-api` on `http://127.0.0.1:8787`
- UI: `make web-ui` on `http://127.0.0.1:5173`
- Browser automation: `npx -y agent-browser`

## Root Cause Found
- Reproduced `Action failed: TypeError: Failed to fetch` in real browser on:
  - onboarding source-pack apply
  - source add/remove
- API logs showed backend `500` caused by FastAPI/Pydantic body resolution errors (`TypeAdapter ... not fully defined`) for local model body params.

## Fix Validation (Real Browser)
- Onboarding tab:
  - `Run preflight` -> success notice.
  - `Apply pack` -> success notice (`added=0, existing=7, errors=0`).
  - `Activate` -> success notice (`Live run started: ...`) and activity card updates.
- Sources tab:
  - `Add` github org -> success notice (`Source add completed.`).
  - `Remove` same org -> success notice (`Source remove completed.`).
- Review tab:
  - `Validate`, `Compute Diff`, `Save Overlay` -> success notice (`Profile overlay saved.`).
- History tab:
  - `Rollback` -> success notice (`Rolled back to ...`).

## Notes
- Onboarding preview flow can run longer than 25s in this environment; UI shows running state and no fetch transport errors were observed after body parsing fix.
