# Cozy Gradient Canvas

Added a warmer layered gradient to the shared web canvas so the graphite/coral product shell feels cozier and more premium.

## What changed
- Updated the global `body` background to use a warmer cream-to-stone gradient with soft coral and graphite haze.
- Updated `.bg-console-canvas` to match the same layered direction so the shell reads as one coherent background system.
- Slightly warmed `bg-panel-subtle` so cards sit naturally over the new canvas.

## Verification
- `npm --prefix web run test`
- `npm --prefix web run build`
- Browser sanity check on the live local app with screenshot validation

## Notes
- The change is intentionally limited to shared background layers.
- Foreground cards and text remain the primary visual focus.
