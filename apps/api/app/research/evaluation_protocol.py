"""Fail-closed validation for an explicitly approved live evaluation manifest."""

from typing import Any


PROTOCOL_ID = "m4-e2e-v1-2026-09-08"
EXPECTED_MODELS = {"openai": "gpt-5-mini", "anthropic": "claude-sonnet-4-5"}
EXPECTED_SLOTS = {
    "M4-CO-1": ("CO", "signal_first"),
    "M4-UT-1": ("UT", "business_first"),
    "M4-TX-1": ("TX", "hybrid"),
}
MAX_CALLS = 18
MAX_COST_CENTS = 200
MAX_CASE_COST_CENTS = 50


def validate_manifest(manifest: dict[str, Any], approved_protocol_id: str) -> None:
    """Reject drift in the cohort or ceilings before live providers are constructed."""
    if approved_protocol_id != PROTOCOL_ID or manifest.get("protocol_id") != PROTOCOL_ID:
        raise ValueError("manifest requires explicit approval of the frozen protocol ID")
    if manifest.get("providers") != EXPECTED_MODELS:
        raise ValueError("provider or model differs from the frozen protocol")
    if manifest.get("search_provider") != "openai_web_search":
        raise ValueError("search provider differs from the frozen protocol")
    if manifest.get("max_live_calls") != MAX_CALLS:
        raise ValueError("live-call ceiling differs from the frozen protocol")
    if manifest.get("max_cost_cents") != MAX_COST_CENTS:
        raise ValueError("total cost ceiling differs from the frozen protocol")

    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_SLOTS):
        raise ValueError("manifest must contain exactly the three frozen cohort slots")
    observed_slots: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("each cohort case must be an object")
        slot = case.get("slot")
        if slot not in EXPECTED_SLOTS or slot in observed_slots:
            raise ValueError("cohort slots must be unique and frozen")
        observed_slots.add(slot)
        expected_state, expected_origin = EXPECTED_SLOTS[slot]
        if (case.get("state"), case.get("origin")) != (expected_state, expected_origin):
            raise ValueError(f"{slot} state or origin differs from the frozen protocol")
        if case.get("max_cost_cents") != MAX_CASE_COST_CENTS:
            raise ValueError(f"{slot} cost ceiling differs from the frozen protocol")
        if not case.get("prelabel") or not case.get("source_urls"):
            raise ValueError(f"{slot} requires a pre-label and source URLs before execution")

    if observed_slots != set(EXPECTED_SLOTS):
        raise ValueError("manifest does not contain every frozen cohort slot")
