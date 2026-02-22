# Proposal: MVP Digest Pipeline (Telegram + Obsidian)

## Why
The user needs a low-noise way to stay current on AI updates without manually scanning many feeds daily.

## Current State
The repository contains a PRD and architecture outline but no implemented pipeline, runtime, or delivery adapters.

## Scope
- Build a single-host MVP pipeline that ingests RSS and YouTube content.
- Rank items by relevance, quality, and novelty.
- Summarize selected items using OpenAI Responses API with deterministic fallback.
- Deliver a daily digest to Telegram and archive a Markdown note in Obsidian.
- Support scheduled daily execution and manual command execution.

## Out of Scope (MVP)
- Fully automated X ingestion.
- Advanced personalization and feedback learning.
- Distributed workers, queue systems, and multi-tenant architecture.

## Risks
- External source instability (feeds/transcripts/API limits).
- LLM outages or latency spikes affecting summary quality/timing.
- Source noise causing weak signal without profile tuning.

## Success Conditions
- A run can complete end-to-end with at least one configured source.
- Telegram and Obsidian outputs are generated from the same selected set.
- Runs are auditable via persisted items, scores, and run metadata.
