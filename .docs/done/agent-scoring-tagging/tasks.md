# Tasks: Agent Scoring and Tagging

- [x] 1.1 Add agent scorer module using OpenAI Responses API.
- [x] 1.2 Define structured scoring+tagging schema.
- [x] 1.3 Add controlled vocab normalization for topic/format tags.

- [x] 2.1 Add `agent_scoring_enabled` profile config.
- [x] 2.2 Wire runtime scoring path to use agent scorer.
- [x] 2.3 Add per-item rules fallback when agent fails.

- [x] 3.1 Extend `Score` model with tags and provider fields.
- [x] 3.2 Extend SQLite `scores` table with JSON tag/provider columns.
- [x] 3.3 Persist tags/provider in `insert_scores`.

- [x] 4.1 Render tags in Obsidian output.
- [x] 4.2 Keep Telegram format stable.

- [x] 5.1 Add/update tests for scoring tags, persistence, and rendering.
- [x] 5.2 Run full test suite.

- [x] 6.1 Write completion summary.
- [x] 6.2 Move change folder to `.docs/done/`.
