"""LangChain-backed LLM helpers for the digest pipeline."""

from digest.llm.client import is_terminal_error, structured_model

__all__ = ["is_terminal_error", "structured_model"]
