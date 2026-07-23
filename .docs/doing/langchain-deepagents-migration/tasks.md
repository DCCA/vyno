# Tasks: LangChain LLM-layer migration

- [x] Confirm `langchain-openai` installable via proxy + baseline 254 tests green with it present
- [x] Add `llm` optional extra to `pyproject.toml`; update `uv.lock`
- [ ] Map test contracts for scorer/summarizer (how they mock OpenAI) — subagent
- [ ] Migrate `ResponsesAPIScorerTagger` internals to `ChatOpenAI.with_structured_output`, preserving contract
- [ ] Migrate `ResponsesAPISummarizer` internals to LangChain, preserving retries/contract
- [ ] Update/extend unit tests to inject a fake LangChain client instead of mocking `urllib`
- [x] DeepAgents fit decision on `quality/online_repair.py`: ADOPTED as an
      opt-in editor agent (`quality/deep_repair.py`, `DeepAgentQualityRepair`),
      selected via `profile.quality_repair_agent: "structured" | "deepagents"`
      (default `structured` to preserve determinism/simplicity). Reuses the
      shared prompt/schema/validation; lazy-imports deepagents so a missing dep
      feeds the existing fail-open path.
- [ ] Full backend suite green (254+) + ruff clean
- [ ] Impeccable UI check on `web/` against its rule set (manual review; plugin not loaded this session)
- [ ] Validate/dogfood on deterministic + mocked path; run `make doctor` if feasible
- [ ] Ship: branch pushed, PR opened, CI green, merge (standing pattern)

## Decisions log

- Preserve class names + `provider` strings + weighting; migrate transport only.
- Lazy-import LangChain inside `__init__` so module import never hard-requires it;
  missing dep feeds existing rules/extractive fallback.
