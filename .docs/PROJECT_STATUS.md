# Project status

Session logbook for Vyno. Newest entry first. Each entry records where the project
stood, what the session changed (with evidence), and what is still open.

For architecture see `.docs/ARCHITECTURE.md`; for product scope see `.docs/PRD.md`.
Completed change folders live in `.docs/done/`.

---

## 2026-08-09 - Console-leftover cleanup, LLM quota fix, scheduler state fix

**Where we were:** `factory-simplification` (2026-07-26, PRs #30-#33) retired the
React + FastAPI console and left Telegram + CLI as the only operator surfaces. What
that program did not remove was everything the console had been built *on*. Digests
were running daily but reporting `status=partial` on every run.

**What we did:**

- **Mapped the runtime architecture** with archify - a validated standalone HTML
  diagram pinned to `f61e3cb`, plus its source spec (`.docs/vyno-current.architecture.{json,html}`, #38).
- **Ran a repo-wide over-engineering audit and implemented every finding** (#38,
  **-2,218 / +134 lines, -3 dependencies**). The dominant find: two console backends
  had outlived the console with zero production callers, kept alive only by their own
  test files - the SQLite timeline subsystem (`web-timeline-observability`: 17 store
  methods, 4 helpers, 3 tables, 4 indexes) and the onboarding catalog / source-packs /
  lifecycle layer (`customer-lifecycle-navigation`). Also cut: the `link_previews`
  cache, `admin_audit`, the `XProvider` ABC + `InboxOnlyXProvider` null object,
  `run_policy.allow_run_override` / `seen_reset_guard` (parsed, validated, documented,
  never read), and `feedparser` / `beautifulsoup4` / `pytest` - all three declared but
  never imported.
- **Fixed the LLM retry storm** (#39). OpenAI reports an exhausted credit balance as
  HTTP 429, so `_classify_fallback_reason` filed it as `rate_limit` and every item
  burned its full retry budget on a call that could never succeed. Measured on the
  real (credit-less) account: **>20 min -> 94 s**, 20 scoring attempts -> 1,
  11 summary attempts -> 1, reason now `quota_exhausted`.
- **Fixed the scheduler state file** (#40). The trigger write spread the whole previous
  state dict, so 14 console-era keys survived every rewrite - the live file still served
  `next_run_at: 2026-07-27` on 2026-08-09, plus a frozen copy of `cadence` / `timezone` /
  quiet hours that `profile.schedule` actually owns. Now writes only the two keys the
  loop owns.
- **Deployed** both containers (`make docker-deploy`), verified in the running image:
  `is_terminal_error` present, timeline methods gone, `quota_exhausted` classification
  live, bot healthcheck green.

**Decisions:**

- **Not everything unreferenced is dead.** `list_run_artifacts` / `list_archived_runs`
  were kept because they back the *Delivered Artifact Persistence* requirement in
  `ARCHITECTURE.md`; `latest_items_for_sources` / `list_feedback` were kept as the read
  sides of live write paths that tests assert against. Deleting a method purely because
  grep finds no caller was the wrong test.
- **`.docs/done/INDEX.md` is the tool that makes deletion safe here.** When code looks
  unused, the answer is usually a retired surface, and naming that surface is the
  evidence - not a guess about speculative design.
- **Real fix over symptom fix on #39.** Correct classification alone would have left
  the waste in place; disabling agent scoring and LLM summaries for the *remainder of
  the run* after the first terminal error is what turned 20 minutes into 94 seconds.
- **Preserved `last_triggered_slot` when pruning the live state file** - dropping it
  would have made the scheduler treat the completed 12:00 slot as pending and deliver
  a duplicate digest. Verified post-prune with a real `evaluate_schedule_tick`: `wait`.

**Pending / next:**

- [ ] **The OpenAI account has no credits** (`insufficient_quota` /
      `credit_balance_exhausted`), unresolved for at least two weeks. Every run degrades
      to rules scoring plus extractive summaries and reports `status=partial`. #39 makes
      that failure fast and correctly labelled but cannot fix it - only adding credits
      restores LLM scoring. **This is the one blocker on digest quality.**
- [ ] Engineer loop: 1 of 3 supervised cycles done (PR #33). Two clean cycles remain
      before scheduling it via cron. Run one with "Run one engineer cycle per AGENTS.md."
- [ ] `data/sources.local.yaml` is git-tracked even though CLAUDE.md declares local
      overlays gitignored. Pre-existing; not touched this session.
- [ ] `source_item_links` is written on every run (`link_source_items`) but nothing in
      production reads it. Left in place deliberately - decide whether it earns its keep
      or joins the console leftovers.
- [ ] `.docs/PRD.md` still lists API token auth modes and secret redaction in API
      payloads under scope. There is no network API; those lines are stale in the same
      way the timeline line was (corrected this session).
