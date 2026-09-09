from copy import deepcopy

import pytest

from app.research.milestone47_ai_protocol import (
    EXPECTED_EXECUTION_MATRIX,
    FROZEN_PACKET_HASH,
    PROTOCOL_ID,
    validate_ai_manifest,
)


@pytest.fixture
def manifest():
    cases = []
    for slot, state, origin in (
        ("M47-CO-1", "CO", "signal_first"),
        ("M47-UT-1", "UT", "business_first"),
        ("M47-TX-1", "TX", "hybrid"),
    ):
        cases.append(
            {
                "slot": slot,
                "state": state,
                "origin": origin,
                "max_cost_cents": 25,
                "evidence_ids": [1, 2],
                "target_subject": "Fictional Person",
                "prelabel": {"relationship": "unclear"},
                "claims": [
                    {
                        "evidence_id": 1,
                        "subject_type": "person",
                        "predicate": "transition",
                    }
                ],
            }
        )
    return {
        "protocol_id": PROTOCOL_ID,
        "frozen_packet_hash": FROZEN_PACKET_HASH,
        "providers": {"openai": "gpt-5-mini", "anthropic": "claude-sonnet-4-5"},
        "tasks": ["business_extraction", "ambiguity_analysis"],
        "max_model_calls": 6,
        "max_cost_cents": 75,
        "max_output_tokens": 3000,
        "execution_matrix": EXPECTED_EXECUTION_MATRIX,
        "cases": cases,
    }


def test_exact_approved_manifest_passes(manifest):
    validate_ai_manifest(manifest, PROTOCOL_ID)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("frozen_packet_hash", "changed", "packet"),
        ("providers", {"openai": "different"}, "provider"),
        ("tasks", ["business_extraction"], "task"),
        ("max_model_calls", 7, "call ceiling"),
        ("max_cost_cents", 76, "cost ceiling"),
    ],
)
def test_protocol_drift_fails_closed(manifest, field, value, message):
    changed = deepcopy(manifest)
    changed[field] = value
    with pytest.raises(ValueError, match=message):
        validate_ai_manifest(changed, PROTOCOL_ID)


def test_explicit_approval_must_match(manifest):
    with pytest.raises(ValueError, match="explicit approval"):
        validate_ai_manifest(manifest, "different-protocol")
