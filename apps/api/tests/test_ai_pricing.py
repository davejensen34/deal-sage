import pytest

from app.ai.pricing import estimated_cost_cents
from app.ai.providers.base import TokenUsage


def test_nonzero_estimated_cost_rounds_up_for_budget_safety():
    assert estimated_cost_cents(
        "openai", "gpt-5-mini", TokenUsage(input_tokens=1, output_tokens=1, total_tokens=2)
    ) == 1


def test_known_anthropic_rate_is_applied():
    assert estimated_cost_cents(
        "anthropic",
        "claude-sonnet-4-5",
        TokenUsage(input_tokens=100_000, output_tokens=10_000, total_tokens=110_000),
    ) == 45


def test_unapproved_model_has_no_implicit_price():
    with pytest.raises(ValueError, match="No frozen price"):
        estimated_cost_cents("openai", "different-model", TokenUsage())
