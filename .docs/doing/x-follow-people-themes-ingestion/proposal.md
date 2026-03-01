# Proposal: X Follow People + Theme Ingestion

## Why
Current X ingestion is manual inbox URL parsing (`x_inbox_path`), which cannot satisfy two core user outcomes:
- users want to follow people and ingest their X content automatically
- users want to follow themes and ingest related X posts (including posts that reference external articles)

## Firehose Alignment
- Brownfield-first: extend existing source registry, connectors, and overlays instead of replacing the ingestion pipeline.
- Iterative delivery: ship people/theme selectors with provider adapters behind configuration flags.
- One logical unit: this change covers only X selector ingestion improvements and its operator controls.

## Problem Statement
- No first-class source types for X authors or X themes.
- No incremental cursor state for X selectors.
- No API/provider abstraction to support different X data acquisition paths.
- Web and bot source workflows cannot add/remove X people/themes as first-class sources.

## Goals
- Add source types so users can track X authors and theme queries directly.
- Preserve current manual inbox path as fallback and migration-safe mode.
- Support incremental ingestion with persisted cursor/checkpoint state.
- Keep existing run/delivery/scoring architecture unchanged from consumer perspective.

## Non-Goals
- No full social graph features (followers/following management UI).
- No guarantee of complete historical backfill in first release.
- No multi-tenant architecture changes.

## User Outcomes
- As a user, I can add/remove X people I want to follow.
- As a user, I can add/remove X themes I want to monitor.
- As a user, I receive digest items from those selectors with the same quality controls used for other sources.

## Success Criteria
- X author and theme selectors can be managed via web UI and Telegram bot commands.
- Runs ingest incremental X items from configured selectors without duplicating old items.
- Source health clearly identifies failures by selector type (`x_author`, `x_theme`, `x_inbox`).
- Existing inbox-only behavior continues to work when selector-based ingestion is disabled.
