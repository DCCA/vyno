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

# Failures that a retry cannot fix: the account is out of credit or the key is
# rejected. OpenAI returns credit exhaustion as HTTP 429, so matching on the
# status alone reads it as a rate limit and burns the whole retry budget on a
# call that can never succeed.
_TERMINAL_ERROR_MARKERS = (
    "insufficient_quota",
    "credit_balance_exhausted",
    "billing_hard_limit_reached",
    "invalid_api_key",
    "account_deactivated",
)


def is_terminal_error(error: object) -> bool:
    """True when an LLM error will keep failing for the rest of this run."""
    text = str(error or "").lower()
    return any(marker in text for marker in _TERMINAL_ERROR_MARKERS)


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

    # use_responses_api pins the Responses endpoint: langchain-openai otherwise
    # routes standard models to Chat Completions, and OpenAI project model
    # allowlists can grant one endpoint while blocking the other.
    llm = ChatOpenAI(
        model=model, timeout=timeout, max_retries=max_retries, use_responses_api=True
    )
    return llm.with_structured_output(schema, method="json_schema", strict=True)
