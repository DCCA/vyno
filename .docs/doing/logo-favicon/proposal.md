# Logo & Favicon: Brand Assets for Web Console

## Why

The web console ships with no custom brand identity — browser tabs show the default Vite icon, there's no logo in the sidebar, and the app has no PWA manifest. This makes the product feel unfinished and harder to identify among open tabs.

## What

Add a minimal brand asset suite:

1. **Logo components** — SVG wordmark and mark for sidebar/header use
2. **Favicon suite** — SVG favicon with PNG fallbacks (16px, 32px, apple-touch-icon)
3. **Multiple favicon variants** — A/B/C options for quick iteration
4. **PWA manifest** — `site.webmanifest` for installable web app metadata
5. **Generation script** — Node script using `sharp` to produce PNG favicons from SVG source

## Scope

- New files only (SVGs, PNGs, manifest, generation script)
- Minimal `index.html` changes (favicon `<link>` tags + title)
- One new React component (`logo.tsx`) for in-app rendering
- No backend changes
