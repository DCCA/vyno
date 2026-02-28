# Proposal: reduce-llm-call-volume

## Why
Recent digest runs are timing out or stalling because run scope and LLM usage are too broad for interactive workflows. Logs show high candidate volume and long summarize phases, which creates excessive provider calls and poor run completion reliability.

## Scope
- Reduce per-run LLM load for live digest runs while preserving digest quality.
- Keep changes brownfield and low-blast-radius in runtime orchestration.
- Add guardrails and telemetry so future regressions are visible.

## Out of scope
- Replacing providers or changing delivery channels.
- Redesigning ranking/scoring heuristics.
