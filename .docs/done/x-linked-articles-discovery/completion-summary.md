# Completion Summary

Extended X selector discovery so trusted author posts can promote outbound links into first-class digest candidates instead of only surfacing social posts.

## What Changed
- Promoted non-X outbound links from `x_author` posts into `link` items.
- Preserved X-native posts while merging duplicate discovery context into canonical article candidates.
- Added endorsement-aware scoring for X-discovered links.

## Verification
- `make test`
- `npm --prefix web run test`
- `npm --prefix web run build`
- Live X integration check for selector fetching

## Risks / Follow-Ups
- `x_theme` promotion remains intentionally out of scope in this version.
