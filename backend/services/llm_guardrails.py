from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """Rough token estimate without external tokenizer dependency."""
    return max(1, len(text) // 4)


def resolve_guardrails(cfg: dict, *, default_timeout: int, default_max_output_tokens: int) -> dict[str, int]:
    return {
        "timeout_seconds": int(cfg.get("timeout_seconds", default_timeout)),
        "max_input_chars": int(cfg.get("max_input_chars", 220000)),
        "estimated_max_input_tokens": int(cfg.get("estimated_max_input_tokens", 55000)),
        "max_output_tokens": int(cfg.get("max_output_tokens", default_max_output_tokens)),
    }


def enforce_llm_limits(
    *,
    phase: str,
    cfg: dict,
    system_text: str = "",
    user_text: str = "",
) -> dict[str, int]:
    combined = f"{system_text}\n{user_text}"
    max_input_chars = int(cfg["max_input_chars"])
    estimated_max_input_tokens = int(cfg["estimated_max_input_tokens"])
    estimated_input_tokens = estimate_tokens(combined)
    if len(combined) > max_input_chars:
        raise RuntimeError(
            f"{phase} aborted before LLM call: input too large "
            f"({len(combined)} chars > {max_input_chars}). Narrow the page selection."
        )
    if estimated_input_tokens > estimated_max_input_tokens:
        raise RuntimeError(
            f"{phase} aborted before LLM call: estimated prompt too large "
            f"({estimated_input_tokens} tokens > {estimated_max_input_tokens}). Narrow the page selection."
        )
    logger.info(
        "[llm] %s guardrails — chars=%d, est_tokens=%d, timeout=%ss, max_output_tokens=%d",
        phase,
        len(combined),
        estimated_input_tokens,
        cfg["timeout_seconds"],
        cfg["max_output_tokens"],
    )
    return cfg


def llm_timeout_message(phase: str, timeout_seconds: int) -> str:
    return (
        f"{phase} stopped after {timeout_seconds}s without a complete LLM response. "
        "Reduce selected pages or choose a lighter model."
    )
