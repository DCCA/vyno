# Completion Summary

Rebuilt the Sources surface around latest-item preview cards so operators can recognize each source by its recent content instead of reading a plain configuration list.

## What Changed
- Added explicit source-to-item linkage in runtime/storage.
- Added cached preview metadata and a source-preview API path.
- Replaced the Sources explanatory cards with image-first preview cards and local actions.

## Verification
- `make test`
- `npm --prefix web run test`
- `npm --prefix web run build`

## Risks / Follow-Ups
- `x_inbox` remains a config-visible fallback card rather than a rich preview source.
