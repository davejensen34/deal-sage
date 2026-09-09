"""Frozen authorization guard for Milestone 4.7 model execution."""

from typing import Any


PROTOCOL_ID = "m4-7-ai-v4-2026-09-09"
FROZEN_PACKET_HASH = "a8d535ed00ade57f3775dd9ad13bcc9b2f48998b077035d1922aa223ebbf84f9"
EXPECTED_MODELS = {"openai": "gpt-5-mini", "anthropic": "claude-sonnet-4-5"}
EXPECTED_SLOTS = {
    "M47-CO-1": ("CO", "signal_first"),
    "M47-UT-1": ("UT", "business_first"),
    "M47-TX-1": ("TX", "hybrid"),
}
MAX_MODEL_CALLS = 6
MAX_COST_CENTS = 75
MAX_CASE_COST_CENTS = 25
MAX_OUTPUT_TOKENS = 3_000
EXPECTED_EXECUTION_MATRIX = [
    {"slot": "M47-CO-1", "provider": "openai", "task": "ambiguity_analysis"},
    {"slot": "M47-CO-1", "provider": "anthropic", "task": "ambiguity_analysis"},
    {"slot": "M47-UT-1", "provider": "openai", "task": "ambiguity_analysis"},
    {"slot": "M47-UT-1", "provider": "anthropic", "task": "ambiguity_analysis"},
    {"slot": "M47-TX-1", "provider": "openai", "task": "ambiguity_analysis"},
    {"slot": "M47-TX-1", "provider": "anthropic", "task": "ambiguity_analysis"},
]


def validate_ai_manifest(manifest: dict[str, Any], approved_protocol_id: str) -> None:
    """Reject changed evidence, models, tasks, or budgets before provider creation."""
    if approved_protocol_id != PROTOCOL_ID or manifest.get("protocol_id") != PROTOCOL_ID:
        raise ValueError("AI execution requires explicit approval of the protocol ID")
    if manifest.get("frozen_packet_hash") != FROZEN_PACKET_HASH:
        raise ValueError("AI execution packet differs from the preflighted evidence")
    if manifest.get("providers") != EXPECTED_MODELS:
        raise ValueError("AI provider or model differs from the frozen protocol")
    if manifest.get("tasks") != ["business_extraction", "ambiguity_analysis"]:
        raise ValueError("AI task set differs from the frozen protocol")
    if manifest.get("max_model_calls") != MAX_MODEL_CALLS:
        raise ValueError("AI call ceiling differs from the frozen protocol")
    if manifest.get("max_cost_cents") != MAX_COST_CENTS:
        raise ValueError("AI cost ceiling differs from the frozen protocol")
    if manifest.get("max_output_tokens") != MAX_OUTPUT_TOKENS:
        raise ValueError("AI output-token ceiling differs from the frozen protocol")
    if manifest.get("execution_matrix") != EXPECTED_EXECUTION_MATRIX:
        raise ValueError("AI execution matrix differs from the frozen protocol")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) != 3:
        raise ValueError("AI protocol requires exactly three cases")
    observed = set()
    for case in cases:
        slot = case.get("slot")
        if slot not in EXPECTED_SLOTS or slot in observed:
            raise ValueError("AI protocol case slots must be unique and frozen")
        observed.add(slot)
        if (case.get("state"), case.get("origin")) != EXPECTED_SLOTS[slot]:
            raise ValueError("AI protocol state or origin differs from preflight")
        if case.get("max_cost_cents") != MAX_CASE_COST_CENTS:
            raise ValueError("AI case cost ceiling differs from the protocol")
        if len(case.get("evidence_ids", [])) != 2 or not case.get("prelabel"):
            raise ValueError("AI cases require two evidence IDs and a human pre-label")
        if not case.get("target_subject"):
            raise ValueError("AI cases require a frozen transition subject")
        claims = case.get("claims")
        if not isinstance(claims, list) or not claims:
            raise ValueError("AI cases require human-authored source claims")
        if any(claim.get("evidence_id") not in case["evidence_ids"] for claim in claims):
            raise ValueError("AI source claims must cite frozen case evidence")
    if observed != set(EXPECTED_SLOTS):
        raise ValueError("AI protocol omits a frozen case slot")
