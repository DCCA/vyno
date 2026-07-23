"""Shared LangChain structured-output client.

The digest calls OpenAI through ``langchain-openai`` structured output rather
than hand-rolled HTTP. ``langchain_openai`` is lazy-imported so importing this
module never hard-requires the optional dependency; a missing key or missing
package raises ``RuntimeError`` and lets callers fall back to their deterministic
paths (rules scorer / extractive summarizer) exactly as a missing
``OPENAI_API_KEY`` did before.
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_TIMEOUT = 30


def structured_model(
    *,
    model: str,
    schema: dict,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = 0,
) -> Any:
    """Return a LangChain runnable whose ``.invoke(messages)`` yields a ``dict``
    matching ``schema`` (an OpenAI-style strict JSON schema).

    Raises ``RuntimeError`` when ``OPENAI_API_KEY`` is unset or
    ``langchain-openai`` is not installed.
    """
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise RuntimeError("OPENAI_API_KEY is required for LLM calls")
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:  # pragma: no cover - exercised via fallback paths
        raise RuntimeError(
            "langchain-openai is required for LLM calls; install the 'llm' extra"
        ) from exc

    llm = ChatOpenAI(model=model, timeout=timeout, max_retries=max_retries)
    return llm.with_structured_output(schema, method="json_schema", strict=True)
