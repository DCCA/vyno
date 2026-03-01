# Design: UI Loading Affordances

## Approach
- Add a derived loading message in `web/src/App.tsx` driven by action state.
- Render a global loading card near the top of the page with spinner + status text.
- Add action-specific loading affordances for:
  - refresh
  - setup preflight and source pack apply
  - source add/remove
  - profile validate/diff/save
  - history rollback

## Notes
- Reuse existing state flags (`loading`, `saving`, `previewLoading`, `runNowLoading`, `activateLoading`) and add minimal action discriminators.
- Keep reduced-motion behavior via existing utility classes.
