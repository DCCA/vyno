# Proposal: Source Grid Status Hover Clarity

## Why
The merged Sources workspace still shows too many always-visible columns and creates scan friction.

## Problem
Operators need fast row-level triage, but `Last Error`, `Last Seen`, and `Hint` consume width and push actions toward clipping.

## Goals
- Keep all existing source-management features.
- Reduce desktop table density.
- Keep diagnostics accessible from each row.
- Keep actions (`Edit`, `Delete`) visible without horizontal scrolling.

## Non-Goals
- No backend API changes.
- No feature removals.
- No source model contract changes.
