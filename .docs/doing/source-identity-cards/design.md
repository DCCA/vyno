# Design: source-identity-cards

## Approach
Implement the preview experience as a full-stack feature. Runtime writes explicit source-item links, SQLite stores link-preview cache records, the web API composes preview rows, and the Sources page renders image-first cards from that API payload.

## Key Decisions
- Store source-item linkage separately from `items` so the same fetched item can belong to multiple configured sources.
- Add cached link previews in the API layer using fetched item URLs and Open Graph/HTML metadata with fallbacks.
- Use a dedicated `/api/source-previews` read endpoint instead of rebuilding cards purely in the frontend.
- Keep source management actions local to each preview card.
- Treat `x_inbox` as a config-visible, non-mutable fallback card.
- Use a single primary preview click target, move badges off unpredictable image overlays, and keep warning/empty states visually lighter than ready-state cards.

## Verification
- Add backend tests for source-item linkage, preview cache storage, and preview endpoint rows.
- Update frontend source-shape tests for preview-card rendering and hierarchy.
- Run `make test`, `npm --prefix web run test`, and `npm --prefix web run build`.
