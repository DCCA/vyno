# Design: Online Must-read Quality Repair

## Runtime Flow
1. Rank items with base scores and quality-learning offsets.
2. Build sections using ranked order.
3. If repair enabled:
   - Candidate pool = top N ranked non-video items.
   - Call quality judge for score + repaired id list.
   - If score < threshold, rewrite Must-read and rebuild Skim.
4. Render Telegram/Obsidian from final sections.

## Judge Contract
- Input includes current Must-read and candidate pool item metadata:
  - `id`, `title`, `url`, `source`, `type`, score, tags, summary fields, text snippet.
- Output strict JSON:
  - `quality_score` (0..100)
  - `confidence` (0..1)
  - `issues` (string list)
  - `repaired_must_read_ids` (exactly 5 ids from candidate pool)

## Persistence
- `run_quality_eval`
  - stores score/issues/before-after ids/model for each run.
- `quality_priors`
  - stores feature weights and update counts for cross-run learning.

## Learning Model
- Feature keys:
  - source family
  - item type
  - topic tags
  - format tags
- Update rule:
  - promoted item features get positive delta
  - demoted item features get negative delta
- Runtime applies decayed and clamped offsets (`half_life_days`, `max_offset`).
- Feedback table contributes additional source/type bias at selection time.

## Safety
- Enforce repaired ids subset of candidate pool.
- Enforce uniqueness and exact count for repaired ids.
- Fail-open mode preserves baseline sections on judge failure.
