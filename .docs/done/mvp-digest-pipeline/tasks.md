# Tasks: MVP Digest Pipeline (Telegram + Obsidian)

- [x] 1.1 Define `sources.yaml` and `profile.yaml` schemas with validation rules.
- [x] 1.2 Define canonical item and summary output models.

- [x] 2.1 Implement RSS connector and fetch window handling.
- [x] 2.2 Implement article text extraction and normalization.
- [x] 2.3 Implement YouTube channel/query connector.
- [x] 2.4 Implement transcript fallback behavior.

- [x] 3.1 Implement exact dedupe by URL/hash.
- [x] 3.2 Implement near-duplicate clustering threshold and representative pick.

- [x] 4.1 Implement weighted scoring engine (relevance/quality/novelty).
- [x] 4.2 Implement profile boosts/penalties and source trust/block logic.

- [x] 5.1 Implement selection policy (Must-read 5, Skim 10, Videos 3-5, total <= 20).
- [x] 5.2 Implement deterministic extractive summarizer.
- [x] 5.3 Implement OpenAI Responses API summarizer adapter.
- [x] 5.4 Implement fallback from Responses API to extractive summarizer.

- [x] 6.1 Implement Telegram renderer and sender.
- [x] 6.2 Implement Obsidian Markdown renderer and vault writer.

- [x] 7.1 Create SQLite schema/tables: `items`, `runs`, `scores`, `seen`.
- [x] 7.2 Persist run metadata, score components, and delivery outcomes.

- [x] 8.1 Implement CLI command `digest run`.
- [x] 8.2 Implement scheduled daily execution entrypoint.

- [x] 9.1 Add unit tests: scoring, dedupe, selection, formatting.
- [x] 9.2 Add integration test: full run with fixture sources.
- [x] 9.3 Add failure-path tests: source failure and Responses API fallback.

- [x] 10.1 Validate all spec scenarios against implementation.
- [x] 10.2 Write completion summary with risks and follow-ups.
- [x] 10.3 Move change folder from `.docs/doing/` to `.docs/done/` when done criteria are met.
