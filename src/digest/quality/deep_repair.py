"""DeepAgents-backed quality repair.

The must-read quality judge is the one genuinely agentic LLM task in the
pipeline: it evaluates an editorial selection, reasons about issues, and
proposes a repaired list under source-cap constraints. This module implements it
as a DeepAgents editor agent that produces the same strict structured decision
as the LangChain path in ``online_repair`` and reuses the same validation, so it
is a drop-in alternative to ``ResponsesAPIQualityRepair``.

``deepagents``/``langchain-openai`` are lazy-imported: a missing dependency or
``OPENAI_API_KEY`` raises ``RuntimeError`` and the runtime falls open, keeping
the original selection exactly as before.
"""

from __future__ import annotations

import os
from typing import Any

from digest.constants import DEFAULT_OPENAI_MODEL
from digest.models import ScoredItem
from digest.quality.online_repair import (
    QualityRepairResult,
    _SCHEMA,
    _SYSTEM_PROMPT,
    _quality_eval_input,
    _validate_repair_inputs,
    build_repair_result,
)


class DeepAgentQualityRepair:
    provider = "deepagents"

    def __init__(
        self,
        model: str = DEFAULT_OPENAI_MODEL,
        timeout: int = 30,
        *,
        agent: Any | None = None,
    ) -> None:
        self.model = model
        self.timeout = timeout
        self._agent = agent or _build_agent(model=model, timeout=timeout)

    def evaluate_and_repair(
        self,
        current_must_read: list[ScoredItem],
        candidate_pool: list[ScoredItem],
        *,
        must_read_max_per_source: int,
        digest_max_per_source: int,
    ) -> QualityRepairResult:
        current_ids, pool_ids = _validate_repair_inputs(
            current_must_read, candidate_pool
        )
        user_text = _quality_eval_input(
            current_must_read=current_must_read,
            candidate_pool=candidate_pool,
            must_read_max_per_source=must_read_max_per_source,
            digest_max_per_source=digest_max_per_source,
        )
        try:
            state = self._agent.invoke({"messages": [("user", user_text)]})
        except Exception as exc:  # normalize agent/transport errors
            raise RuntimeError(f"Quality repair failed: {exc}") from exc
        parsed = (state or {}).get("structured_response")
        return build_repair_result(
            parsed, current_ids=current_ids, pool_ids=pool_ids, model=self.model
        )


def _build_agent(*, model: str, timeout: int) -> Any:
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise RuntimeError("OPENAI_API_KEY is required for quality repair")
    try:
        from deepagents import create_deep_agent
        from langchain_openai import ChatOpenAI
    except ImportError as exc:  # pragma: no cover - exercised via fallback paths
        raise RuntimeError(
            "deepagents + langchain-openai are required for the deepagents "
            "quality-repair agent; install the 'llm' extra"
        ) from exc

    chat = ChatOpenAI(model=model, timeout=timeout, max_retries=0)
    return create_deep_agent(
        model=chat,
        system_prompt=_SYSTEM_PROMPT,
        response_format=_SCHEMA,
    )
