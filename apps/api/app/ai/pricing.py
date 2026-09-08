"""Frozen evaluation prices used for conservative per-call cost attribution."""

from math import ceil

from app.ai.providers.base import TokenUsage


# These rates belong to the approved m4-e2e-v1-2026-09-08 protocol. A later
# model or price requires a new protocol rather than silently changing history.
MODEL_RATES_PER_MILLION = {
    ("openai", "gpt-5-mini"): (0.25, 2.00),
    ("anthropic", "claude-sonnet-4-5"): (3.00, 15.00),
}


def estimated_cost_cents(provider: str, model: str, usage: TokenUsage) -> int:
    """Round non-zero estimated spend up to one cent for fail-safe budgeting."""
    rates = MODEL_RATES_PER_MILLION.get((provider, model))
    if rates is None:
        raise ValueError("No frozen price exists for this provider and model")
    input_tokens = usage.input_tokens or 0
    output_tokens = usage.output_tokens or 0
    dollars = (input_tokens * rates[0] + output_tokens * rates[1]) / 1_000_000
    return ceil(dollars * 100) if dollars else 0
