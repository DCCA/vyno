# Web Console Route UX Restructure

## What Changed
- Replaced the single-surface console flow with route-based workspaces for dashboard, run center, onboarding, sources, profile, review, timeline, and history.
- Split the previous `web/src/App.tsx` monolith into route-aware shell/controller logic plus feature modules under `web/src/features/`.
- Added shared frontend boundaries for navigation, API access, utility helpers, shared types, page headers, and local inline notices.
- Preserved existing backend API usage and local-feedback behavior while improving workflow separation and URL-addressable workspace state.
- Updated frontend source-shape tests to validate the new route/workspace architecture and retained UX contracts.

## Verification
- `npm --prefix web run test`
- `npm --prefix web run build`
- Manual browser smoke test:
  - verified direct route navigation for all workspaces
  - verified a browser-triggered `Run now` populated Timeline
  - verified Sources query state persisted in URL
  - captured desktop and mobile screenshots for all routes under `.runtime/qa-screens/`

## Risks
- Route-based navigation now depends on SPA history fallback behavior from the host environment.
- `App.tsx` still coordinates most network actions; a future pass can push more state ownership fully into feature-local hooks.

## Follow-Ups
- Review the captured screenshots and tighten any remaining spacing or density issues per route.
- Consider a second refactor pass to move more controller logic from `App.tsx` into feature-local data hooks.
