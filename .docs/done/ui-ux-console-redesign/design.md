# Design: UI UX Console Redesign

## Inputs and Design Direction
- Use the `ui-ux-pro-max` skill guidance as design intelligence input (task-first flow, strong status affordances, accessibility checks, responsive behavior).
- Keep visual language operational and high-signal: neutral slate base, teal primary actions, amber warning accents, clear destructive semantics.
- Typography stack:
  - Display: Space Grotesk
  - Body: IBM Plex Sans
  - Mono: JetBrains Mono

## Architecture Deltas
- Frontend only (no API contract changes).
- Refactor `web/src/App.tsx` into mode-first rendering:
  - Setup Journey (default for incomplete onboarding)
  - Manage Workspace (advanced operations)
- Continue polling and mutation handlers already in place.
- Keep existing endpoint usage in `src/digest/web/app.py` unchanged.

## Setup Journey UX
- Show setup progress and next-step context at the top.
- Render onboarding steps as actionable cards with status and details.
- Provide in-context controls for preflight, preview, activate, and source pack application.
- Keep preview artifacts visible within setup mode.

## Manage Workspace UX
- Preserve advanced capabilities via focused tabs:
  - Sources
  - Profile
  - Review
  - History
- Include clear path back to setup mode when onboarding remains incomplete.

## Styling and Motion
- Update tokens in `web/src/index.css` and `web/tailwind.config.ts` for deliberate visual hierarchy.
- Add layered background and stronger card surfaces without dark-mode conversion.
- Respect reduced-motion preferences for loading/progress animations.

## Verification Plan
- `make test`
- `make web-ui-build`
- Browser E2E with `npx -y agent-browser` across onboarding and manage workflows.
