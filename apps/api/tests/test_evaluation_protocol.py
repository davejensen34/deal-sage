import copy

import pytest

from app.research.evaluation_protocol import PROTOCOL_ID, validate_manifest


@pytest.fixture
def manifest():
    return {
        "protocol_id": PROTOCOL_ID,
        "providers": {
            "openai": "gpt-5-mini",
            "anthropic": "claude-sonnet-4-5",
        },
        "search_provider": "openai_web_search",
        "max_live_calls": 18,
        "max_cost_cents": 200,
        "cases": [
            {
                "slot": slot,
                "state": state,
                "origin": origin,
                "max_cost_cents": 50,
                "prelabel": {"research_disposition": "needs_more_research"},
                "source_urls": [f"https://example.test/{slot.lower()}"],
            }
            for slot, state, origin in (
                ("M4-CO-1", "CO", "signal_first"),
                ("M4-UT-1", "UT", "business_first"),
                ("M4-TX-1", "TX", "hybrid"),
            )
        ],
    }


def test_frozen_manifest_is_accepted(manifest):
    validate_manifest(manifest, PROTOCOL_ID)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("max_live_calls", 19, "call ceiling"),
        ("max_cost_cents", 201, "cost ceiling"),
        ("search_provider", "another_provider", "search provider"),
    ],
)
def test_protocol_drift_is_rejected(manifest, field, value, message):
    changed = copy.deepcopy(manifest)
    changed[field] = value
    with pytest.raises(ValueError, match=message):
        validate_manifest(changed, PROTOCOL_ID)


def test_case_replacement_cannot_change_slot_shape(manifest):
    manifest["cases"][0]["origin"] = "business_first"
    with pytest.raises(ValueError, match="state or origin"):
        validate_manifest(manifest, PROTOCOL_ID)


def test_manifest_requires_matching_explicit_approval(manifest):
    with pytest.raises(ValueError, match="explicit approval"):
        validate_manifest(manifest, "unapproved-protocol")


def test_each_case_requires_prelabel_and_sources(manifest):
    manifest["cases"][2]["source_urls"] = []
    with pytest.raises(ValueError, match="pre-label and source URLs"):
        validate_manifest(manifest, PROTOCOL_ID)
