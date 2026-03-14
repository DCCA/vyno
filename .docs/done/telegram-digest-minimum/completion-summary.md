# Completion Summary

Expanded Telegram rendering so the digest reliably surfaces at least ten selected items while preferring source diversity from the existing selected pool.

## What Changed
- Replaced the Must-read-only Telegram selector with a renderer-local pass over Must-read, Skim, and Videos.
- Added source-diversity-aware ordering before backfilling to ten items.
- Locked the behavior with renderer tests.

## Verification
- `make test`

## Risks / Follow-Ups
- This change affected Telegram rendering only and intentionally did not change upstream digest selection.
