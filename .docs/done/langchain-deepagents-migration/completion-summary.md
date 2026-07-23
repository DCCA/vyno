# Completion summary: LangChain + DeepAgents LLM-layer migration

**Status:** shipped (PR #17, merged to `master`).

## What changed

Migrated the three OpenAI call sites from hand-rolled `urllib` + Responses-API
JSON handling to a shared **LangChain** structured-output client, and added an
opt-in **DeepAgents** implementation for the one genuinely agentic task.

- `src/digest/llm/client.py` (new) — `structured_model(...)` builds a
  `langchain_openai` structured-output runnable; lazy-imported so importing the
  module never hard-requires the optional dep.
- `src/digest/scorers/agent.py` — `ResponsesAPIScorerTagger` now calls the
  LangChain client; provider `"agent"`, weighting (`rel*6`, `qual*3`, `nov`),
  vocab and tag normalization preserved.
- `src/digest/summarizers/responses_api.py` — `ResponsesAPISummarizer` now uses
  LangChain; `retries` maps to `ChatOpenAI(max_retries=...)` (retries 429/5xx/
  timeout, not 4xx). Provider `"openai_responses"` and `Summary` shape preserved.
- `src/digest/quality/online_repair.py` — `ResponsesAPIQualityRepair` migrated;
  extracted shared `build_repair_result()` / `_validate_repair_inputs()`.
- `src/digest/quality/deep_repair.py` (new) — `DeepAgentQualityRepair`, a
  DeepAgents editor agent for the must-read quality judge, selectable via
  `profile.quality_repair_agent` (`"structured"` default | `"deepagents"`).
  Reuses the shared prompt/schema/validation; lazy-imports `deepagents`.
- `pyproject.toml` — optional `llm` extra (`langchain-openai`, `deepagents`);
  `uv.lock` updated. CI installs via `uv sync --all-extras`.

## Contracts & behavior preserved

- Class names, `provider` strings, constructor signatures, and
  `Score`/`Summary`/`QualityRepairResult` shapes unchanged → runtime wiring and
  all class-level test mocks untouched.
- Graceful degradation intact: missing `OPENAI_API_KEY` **or** missing
  `langchain-openai`/`deepagents` raises `RuntimeError` and the pipeline falls
  back to rules scorer / extractive summarizer / fail-open repair — exactly as a
  missing key behaved before.
- Net ~300 lines of hand-rolled transport/parse/retry deleted.

## Verification

- Backend: 258 unit tests pass; `ruff check src tests` clean. Only
  `tests/test_responses_api_summarizer.py` (the sole urllib-coupled test) was
  rewritten to inject a fake client; `tests/test_deep_repair.py` added.
- Frontend: 24 tests pass; `npm run build` green (no `web/` files changed).
- Impeccable UI check: `impeccable detect web/src` → 0 anti-patterns (detector
  verified active). See this change's earlier `ui-check.md` (git history).
- Functional UI: all 8 routes rendered in headless Chromium against the running
  API (live data: 25 sources, health OK, run state idle).
- CLI dogfood: `digest … doctor` clean; DeepAgents agent constructs against the
  real `ChatOpenAI` + schema and exposes `structured_response`.

## Known gaps / follow-ups

- **Live LLM calls were not exercised** (no `OPENAI_API_KEY` in the build
  environment; external egress blocked). Contract tests use injected fakes. The
  first run with a real key is the true end-to-end proof. Runbook:
  ```bash
  export OPENAI_API_KEY=sk-...            # a valid key
  make live                               # exercises LangChain scorer+summarizer
  # to exercise the DeepAgents judge, set in config/profile.yaml (or overlay):
  #   quality_repair_agent: deepagents
  ```
- **Dependency weight:** LangChain + DeepAgents pull a large transitive tree;
  mitigated by the optional `llm` extra + lazy import (base install stays
  PyYAML/FastAPI/uvicorn).
- **Supply chain (`pip-audit`, full env incl. extras):** 14 advisories across 6
  packages — all in pre-existing/transitive deps (`starlette` via FastAPI,
  `soupsieve` via beautifulsoup4, `click`/`idna`/`pygments`/`pytest`). **None in
  the added LLM libraries** (langchain/deepagents/langgraph/pydantic/openai/
  tiktoken). Recommend a separate framework-bump pass for the FastAPI/starlette
  stack; not in scope for this change.
- **DeepAgents kept opt-in** (`quality_repair_agent` defaults to `structured`)
  to preserve determinism/simplicity; revisit if a live run shows the agent
  meaningfully outperforms the structured judge.

## Live-run verification (2026-07-23)

The deferred live run was executed (`make live` + a `preview_mode=True` run).
Pipeline mechanics are green end to end: ingest, dedupe, selection, Telegram
delivery, Obsidian archive, run history, and fail-open degradation all behaved
as designed. The LLM path itself surfaced three issues:

1. **Fixed - Docker prod missing LLM deps:** `requirements.txt` (used by the
   Dockerfile) did not include `langchain-openai`/`deepagents`, so deployed
   bot/scheduler runs silently fell back to rules scoring + extractive
   summaries (`llm_coverage=0.0`, status `partial`).
2. **Fixed - local setup missing LLM deps:** `scripts/setup.sh` ran plain
   `uv sync` (and `pip install -e .`), which skips the `llm` extra. Now
   `uv sync --all-extras` / `pip install -e '.[runtime,llm]'`.
3. **Fixed - model + endpoint access:** the OpenAI project allowlist was
   scoped to the deprecated `gpt-5.1-codex-mini` (every call 404'd). After the
   dashboard allowlist was widened, defaults moved to `gpt-4.1-mini`
   (constants, `config/profile.yaml`, `.env.example`). A second trap surfaced:
   the project allowlist granted models on the Responses endpoint while
   blocking Chat Completions, and `langchain-openai` routes standard models to
   Chat Completions by default. The shared client and the DeepAgents agent now
   pin `use_responses_api=True`, matching the pre-migration Responses-only
   behavior. With that, both quality judges (LangChain structured and
   DeepAgents) passed live contract tests, and the full pipeline ran with
   `llm_coverage=1.0`.
