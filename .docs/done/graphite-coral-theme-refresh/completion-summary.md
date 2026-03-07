# Graphite Coral Theme Refresh

Updated the shared web UI theme to the approved `Graphite + Coral` direction from the theme lab.

## What changed
- Replaced the old blue/amber global token set with a graphite/coral light theme.
- Swapped production typography to `Archivo` for display, `Public Sans` for UI text, and `IBM Plex Mono` for technical strings.
- Removed the noisy page grid overlay and simplified the canvas to a much quieter background treatment.
- Refreshed shared primitives so cards, buttons, badges, and workspace headers match the new palette and accent behavior.
- Tightened the top shell header breakpoint after browser validation exposed a desktop text-wrapping regression.

## Verification
- `npm --prefix web run test`
- `npm --prefix web run build`
- Browser sanity check on local app at desktop width with screenshot validation

## Risks / follow-up
- The refresh is intentionally token-first, so any future color polish should continue through shared primitives instead of page-specific overrides.
