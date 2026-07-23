# Proposal: Migrate the LLM layer to LangChain (and DeepAgents where it fits)

## Context

The digest pipeline calls the OpenAI Responses API from two hand-rolled
`urllib` modules:

- `src/digest/scorers/agent.py` — `ResponsesAPIScorerTagger` (`provider="agent"`),
  scores/tags items. ~244 lines, most of it manual HTTP + JSON-extraction +
  schema validation + numeric clamping.
- `src/digest/summarizers/responses_api.py` — `ResponsesAPISummarizer`
  (`provider="openai_responses"`), summarizes selected items. ~158 lines, most of
  it manual HTTP + retries + JSON-extraction.

Both are already wrapped in graceful-degradation paths in `runtime.py`:

- Scorer: `runtime.py:582` constructs it inside `try/except`; on failure the run
  falls back to the rule-based scorer (`pipeline/scoring.py`).
- Summarizer: `runtime.py:1158` constructs it inside `try/except` and wraps it in
  `FallbackSummarizer(primary=..., fallback=ExtractiveSummarizer())`
  (`pipeline/summarize.py`), which also falls back on any per-item exception.

## Goal (RFC 2119)

- The system SHALL invoke OpenAI through `langchain-openai` structured output
  instead of hand-rolled `urllib` + JSON parsing.
- The migration MUST preserve every externally observable contract:
  class names, `provider` strings (`"agent"`, `"openai_responses"`), constructor
  signatures, `Score`/`Summary` output shapes, and the scorer's weighting
  (`relevance = rel10*6`, `quality = qual10*3`, `novelty = nov10`).
- The migration MUST preserve graceful degradation: with no `OPENAI_API_KEY`
  **or** no `langchain-openai` installed, construction raises `RuntimeError` and
  the pipeline falls back to rules/extractive exactly as today.
- The change SHOULD reduce net line count and hand-rolled parsing/validation,
  serving the primary goal of simplicity + maintainability.
- All 254 backend tests and the frontend suite MUST stay green.

## Design

1. **Dependency**: `langchain-openai` added as an optional `llm` extra in
   `pyproject.toml`. CI installs it via `uv sync --all-extras`. It is
   **lazy-imported inside `__init__`** so importing the module never requires
   LangChain; a missing dep raises `RuntimeError` and feeds the existing
   fallback — mirroring the current `OPENAI_API_KEY` guard.

2. **Scorer** (`scorers/agent.py`): replace the `urllib` request + manual
   `_extract_json_output`/`_validate_agent_payload` with
   `ChatOpenAI(...).with_structured_output(schema)`. Keep `TOPIC_VOCAB`,
   `FORMAT_VOCAB`, tag normalization, clamping, and weighting untouched — those
   are business logic, not transport. The model call is factored behind a small
   seam so tests inject a fake structured-output client without hitting the wire.

3. **Summarizer** (`summarizers/responses_api.py`): same treatment. LangChain's
   built-in retry (`.with_retry`) replaces the hand-rolled retry loop; the
   `retries`/`retry_backoff_seconds` constructor args are preserved for
   compatibility and mapped onto it.

4. **DeepAgents**: evaluated against `quality/online_repair.py`. DeepAgents earns
   its weight only where multi-step, tool-using agent behavior is real; a single
   structured call does not qualify. Decision recorded in `tasks.md` after the
   repair-loop review — if it does not fit, DeepAgents is intentionally **not**
   added (forcing a heavy dep onto a single-shot call would violate the
   simplicity goal, and "keep it out" is a defensible outcome of "use it where it
   fits").

## Non-goals

- No change to selection, dedupe, delivery, storage, or the rules scorer.
- No change to prompts' intent or the scoring rubric.
- No new user-facing config (provider selection stays as-is).

## Risks

- **Dependency weight**: LangChain pulls a large transitive tree (pydantic,
  openai SDK, tiktoken, tenacity, …). Mitigated by keeping it an optional extra +
  lazy import; base install stays PyYAML/FastAPI/uvicorn.
- **Behavioral drift** in structured output vs. the Responses `json_schema`
  format. Mitigated by keeping identical schemas and asserting output shape in
  tests with mocked clients.
- **No live API key in this environment** → validation is on the deterministic
  path + mocked LLM clients, not a live run. Called out honestly; not claimed as
  a live dogfood.
