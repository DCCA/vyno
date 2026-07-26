# Proposal: Vyno as a self-improving digest factory

**Status:** DRAFT v2 (ponytail-reviewed) - awaiting your approval. Tell Claude your section 9 picks, or edit the markdown directly.
**Date:** 2026-07-26
**Change folder:** `.docs/doing/factory-simplification/` (`tasks.md` will be written after approval, scoped to the options you pick)

---

## 1. Summary

Cut vyno down to its production line, then make the line maintain itself: a scheduled agent (the "engineer") reads run reports and feedback, and ships one improvement PR per cycle. You review PRs; that is the whole human job.

Two moves, in order:

1. **Simplify** - remove the ~50% of the codebase that is operator tooling and dead flexibility, not product.
2. **Self-improve** - add a small, guarded agent loop on top of the CI and quality plumbing that already exists.

## 2. The core value we protect

One curated AI-news digest per day, scored and deduplicated against your profile, delivered to **Telegram** (mirrored to **Obsidian**), that **gets better as you react to it**.

These MUST NOT regress: delivery reliability, the scoring/dedupe quality, the feedback-to-ranking loop, and source coverage (RSS, YouTube, GitHub, X).

**Top user journey (your call, 2026-07-26): suggesting a new ingest MUST stay easy.** You find something good, you add it in seconds from where you already are. Today the paths are the web Sources page, `/source` in Telegram, and the overlay YAML; whatever survives Tier 2 MUST keep a path this easy or easier. See the top-journey upgrade in section 4.

Everything else in the repo is support machinery and is on the table.

## 3. Where the code actually is (audit, 2026-07-26)

| Area | LOC | Note |
|---|---|---|
| Backend `src/digest/` | 14,729 | ops 3,066 · top-level 3,040 · web 2,943 · storage 1,789 · connectors 1,401 · pipeline 811 · rest 1,679 |
| Frontend `web/src/` | 7,455 | `App.tsx` alone is 1,861 (all state for 8 pages in one component) |
| Tests | 6,587 py + 369 mjs | strong suite - this is the safety rail the agent loop stands on |
| `video/` | 3,842 tracked | a Remotion marketing video project, zero coupling to the digest |

Key audit facts:

- **The self-improvement seed already exists and closes.** Feedback (web buttons or Telegram `/feedback`) writes `feedback` + `quality_priors` in SQLite; the next run reads them as rank offsets with 14-day decay; the LLM quality-repair pass logs `run_quality_eval` per run. We build on this, not beside it.
- **The operator surface exists three times** for one operator: React console (7,455), FastAPI control plane (2,943, all 46 routes still in one 1,692-line `app.py`), and Telegram command wizards (~900 of `telegram_commands.py`'s 1,661 lines are chat-native form plumbing duplicating the web console).
- Dead flexibility verified unused: a second quality-repair implementation (`deepagents`) no config selects; `render_mode`/`obsidian_naming` options with one value ever used; a two-provider X class hierarchy for an env var that holds one value; `youtube_queries` path with zero configured queries; 5 dead functions; 9 helpers duplicated across files.

## 4. The cuts

### Tier 0 - hygiene, zero behavior change (~3,980 lines) - proposed regardless of Tier 2

| Cut | Lines | Detail |
|---|---|---|
| `git rm -r video/` | 3,842 | Remotion project, zero coupling; git history is the backup - resurrect into a sibling repo only if it's ever touched again. Also frees 388M of untracked `node_modules` |
| Delete 5 dead functions | ~130 | `build_rank_overrides`, `score_items`, `edit_telegram_reply_markup`, `_build_digest_lines`, `_build_context_lines` - zero call sites |
| Delete `requirements.txt` | 7 | contradicts `pyproject.toml` extras; `uv.lock` is the real lock |

Not a dedicated pass (ponytail): the 9 duplicated helpers (`_read_yaml_dict` x3, `_clean_text` x3, ...) get consolidated opportunistically when a file is already open for other work. Unused TS exports and the empty `features/review/` dir only matter under Option B/C - Option A deletes `web/` wholesale.

### Tier 1 - dead flexibility (~300 lines) - proposed regardless of Tier 2

| Cut | Lines | Detail |
|---|---|---|
| Remove `deepagents` repair path + dependency | ~200 | `quality_repair_agent` is set nowhere; structured repair stays - kills a real dependency |
| Remove `render_mode` / `obsidian_naming` options | ~70 | Telegram accepts `render_mode` and never reads it; one value ever used - dead flags mislead the engineer agent |
| Remove `youtube_queries` path | ~30 | zero configured, undocumented best-effort URL |

Dropped from the plan after ponytail review: collapsing the X provider hierarchy (~250) and shrinking `runtime_support.py` (~40) - refactor churn on working code with zero product effect. Leave them alone until they hurt.

**Inline decision:** X currently ingests from 1 author + 1 theme + 1 inbox URL, with its own USD cost accounting.
- [ ] Keep X (leave the code alone - no refactor until it hurts)
- [ ] Drop the X connector entirely (~650+ lines; re-add later if X earns its keep)

### Tier 2 - the strategic cut: one operator surface, pick one

**Option A - Telegram-first (recommended): retire the web console.**
Delete `web/` (React, 7,455), `src/digest/web/` (FastAPI, 2,943), frontend tests/toolchain/make targets; the docker scheduler service keeps the scheduler and drops the API. Telegram becomes the single interactive surface (commands and wizards stay as-is; feedback keeps flowing via `/feedback`). Ops visibility moves to `/status`, `/history`, `/doctor` and the brief's SQL queries (section 6).
*Why recommended:* one operator (you), delivery already lives in Telegram, and the engineer agent needs CLI + DB + PRs, not a GUI. Removes ~10,700 LOC plus the whole React/Vite dependency tree. Fully reversible via git.
*Cost:* you lose the visual timeline/history/source-health pages.

**Option B - freeze the web console.**
Keep it running, invest zero: no refactors, agents MUST NOT touch `web/` or `src/digest/web/`. Revisit in 60 days. Smallest step, but the factory keeps carrying ~10,400 LOC of frozen surface, and the engineer's improvement territory shrinks accordingly.

**Option C - keep the web console invested.**
Then the audit's refactors become Tier 1 work instead: split `App.tsx` state into its feature dirs (~1,200), real router split of `app.py` (~600), gut the duplicated Telegram wizard plumbing (~900, keeping plain commands). Keeps all three surfaces at lower cost, but keeps three surfaces.

### Top-journey upgrade (small, new): paste-a-link ingest suggestion

Whatever the Tier 2 pick: `/source add <url-or-handle>` in Telegram detects the type (YouTube channel, GitHub repo/org/topic, X author, else RSS autodiscovery), preflights it, and asks one confirm before writing the overlay - no type flag, no wizard steps. ~150-200 LOC reusing the existing preview/preflight helpers in `web/sources.py` (under Option A those helpers move to `ops/`; they don't die with the console).

If preflight finds no connector that can handle the link, the bot records it as an ingest suggestion (existing `feedback` table, `label='ingest_suggestion'`, zero schema change) and says so. The engineer reads pending suggestions each cycle - a new connector type becomes an engineer PR, not a dead end.

Totals: Tiers 0+1 remove ~4,300 lines. With Option A the whole change removes **~15,000 of ~22,000 non-test LOC**, and the removed surfaces take their tests with them.

## 5. Target architecture: the factory

```
        sources (rss / youtube / github / x)
                      |
   [PRODUCTION LINE]  ingest > normalize > dedupe > score > select > deliver > archive
                      |                                        ^
   [QC - exists]      feedback + run_quality_eval + priors ----+   (runtime loop, per run)
                      |
   [ENGINEER - new]   scheduled agent reads reports/feedback > one improvement PR > CI > you merge
```

The production line and the runtime QC loop do not change. The factory is a framing, not a rewrite: no renames, no new frameworks, no restructure beyond the cuts above.

## 6. The engineer (the self-improvement loop)

The one genuinely new piece, kept deliberately small:

- **An "Engineer" section in `AGENTS.md`** - the standing brief: the exact read-only SQL for its inputs (run history, `run_quality_eval`, `feedback`, `quality_priors`, source errors), the guardrails below, and the definition of done. No new CLI, no new directory; if the queries ever drift or break, promote them to a `digest report` subcommand then.
- **A scheduled run** - Claude Code scheduled agent (or keikaku routine). Starts manual; cron only after 3 supervised cycles.

### Requirements

- **R1** - The engineer MUST read only the brief's listed queries (read-only SQL over the run/feedback/quality tables), CI status, and the repo itself as inputs.
- **R2** - One improvement PR per cycle, smallest change that addresses the strongest signal: source add/demote, threshold tweak, prompt change, small code fix, doc sync. The PR body MUST cite the evidence (metrics before, expected effect) and show `make test` output.
- **R3** - The engineer MUST NOT merge. You merge; CI (260 backend tests, frontend suite while it exists, security scans) gates every PR. No auto-merge class exists in v1.
- **R4** - Hard fences: MUST NOT touch `.env` or any secret, MUST NOT change DB schema, MUST NOT alter delivery credentials/chat targets, MUST follow FIREHOSE for anything non-trivial.
- **R5** - If the signals show nothing actionable, the engineer MUST end the cycle with no PR. Silence is success; it MUST NOT invent work.

### Scenarios

- Given 3 of the last 7 runs are `partial` with timeouts from one RSS source, when the engineer runs, then it opens a PR demoting or removing that source, citing the error counts, and touches nothing else.
- Given all runs green and no new feedback since the last cycle, when the engineer runs, then it opens no PR and logs "no action".
- Given persistently low `run_quality_eval` scores traced to the scoring prompt, when the engineer runs, then it opens a PR tuning the prompt with before-scores in the body, and the change ships only after tests pass and you merge.
- Given a pending ingest suggestion no existing connector can handle, when the engineer runs, then it opens a PR adding the minimal connector for it (or replies on the suggestion with why not), following FIREHOSE for the non-trivial case.

## 7. Deliberately not doing (YAGNI)

- No multi-product/multi-tenant factory - one digest, one reader.
- No auto-merge, no agent-run deploys.
- No new frameworks, no pipeline rewrite, no repo rename/restructure.
- No dashboard for the engineer - the PR list is the dashboard.

## 8. Side findings (flagged, not part of this change)

- `digest-live.db` is 93M in the working tree and growing; worth a retention/vacuum pass someday.
- `.env` holds a live X API bearer token in plaintext (gitignored, correctly, but on disk).
- A literal `~/` directory sits at repo root (untracked artifact of an unquoted `~`); safe to remove.

## 9. Approval

Tick and save (inkwell autosaves), or tell Claude directly:

- [ ] **Tier 0** hygiene cuts
- [ ] **Tier 1** dead-flexibility cuts
- [ ] X connector: keep (collapsed) - or tick the drop box in section 4
- [ ] **Tier 2: Option A** - retire web console (recommended)
- [ ] **Tier 2: Option B** - freeze web console
- [ ] **Tier 2: Option C** - keep and refactor
- [ ] **Paste-a-link ingest suggestion** (top-journey upgrade, section 4)
- [ ] **Engineer loop** as specced in section 6
- Notes / changes:

## 10. Rollout (after approval)

Three PRs, each branch + tests green before merge, per the repo's standing workflow:

1. **Hygiene** - Tier 0: `git rm -r video/`, dead functions, `requirements.txt`.
2. **Cuts** - your Tier 2 pick plus the surviving Tier 1 cuts, plus the paste-a-link ingest suggestion (it lands with whichever surface survives).
3. **Engineer** - the `AGENTS.md` brief, then the first supervised cycle.

Scheduling is not a phase: after 3 clean supervised cycles, it's one cron line.
