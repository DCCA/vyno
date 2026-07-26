# Tasks: factory-simplification

Approved 2026-07-26: Tier 0 + Tier 1, keep X (no refactor), Tier 2 Option A, paste-a-link ingest suggestion, engineer loop. Process: codex review + multi-agent review workflow per PR; dogfood before ship; merge only on green CI.

## PR 1 - Hygiene (Tier 0)

- [x] Scout: every reference to `requirements.txt` (Dockerfile, CI, scripts, docs) and to the 5 dead functions (verify zero call sites incl. tests)
- [x] `git rm -r video/` (+ remove untracked `video/node_modules` from disk)
- [x] Delete `requirements.txt`; repoint any consumer to `pyproject.toml`/`uv`
- [x] Delete dead functions: `build_rank_overrides`, `score_items`, `edit_telegram_reply_markup`, `_build_digest_lines`, `_build_context_lines`
- [x] Remove stray untracked `~/` dir at repo root (local cleanup, not in PR)
- [x] Commit proposal.md + tasks.md with this PR
- [x] Validate (tests + ruff), codex review, CI green, merge

## PR 2 - Cuts (Option A + Tier 1 + paste-a-link)

- [ ] Scout: all references to `web/`, `src/digest/web/`, `DIGEST_WEB_*` (Makefile, compose.yaml, Dockerfile, scripts/start-app.sh, cli.py `web` cmd, CI workflows, docs, tests)
- [ ] Move preflight/preview helpers needed by paste-a-link from `src/digest/web/sources.py` (+ `link_preview.py` if needed) into `ops/`
- [ ] Delete `web/` (React) + `web/tests/` + frontend toolchain refs (Makefile, CI frontend job, package caches in docs)
- [ ] Delete `src/digest/web/` (FastAPI); remove `web` from cli.py; reshape `digest-scheduler` docker service to scheduler-only; update `scripts/start-app.sh` or remove
- [ ] Tier 1: remove `deepagents` path (`quality/deep_repair.py`, test, config keys, dependency)
- [ ] Tier 1: remove `render_mode` / `obsidian_naming` options (config + delivery); keep the actually-used behaviors
- [ ] Tier 1: remove `youtube_queries` path
- [ ] Paste-a-link (TDD): `/source add <url-or-handle>` - type detection (yt channel / gh repo-org-topic / x author / rss autodiscovery), preflight, one confirm, overlay write; unknown -> `feedback` row `label='ingest_suggestion'`
- [ ] Remove tests covering deleted surfaces; keep/port anything covering kept logic
- [ ] Update docs: README, CLAUDE.md, AGENTS.md, .docs/ARCHITECTURE.md
- [ ] Dogfood: `make doctor` + preview digest run (no delivery) + paste-a-link handler exercised via test harness
- [ ] Validate, review workflow (multi-dimension + adversarial verify), codex review, CI green, merge

## PR 3 - Engineer

- [ ] AGENTS.md "Engineer" section: exact read-only SQL (verify against `storage/schema.py`), guardrails R1-R5, one-PR-per-cycle, no-action-is-success
- [ ] Dogfood: run one supervised engineer cycle against the real DB; record outcome
- [ ] Move `.docs/doing/factory-simplification/` -> `.docs/done/` keeping only `completion-summary.md`; update INDEX.md
- [ ] Validate, codex review, CI green, merge

## Wrap

- [ ] Final dogfood: `make doctor` + preview run on master
- [ ] Report with evidence (test output, PR links, LOC delta)
