from copy import deepcopy
from datetime import date
from hashlib import sha256
import json

import pytest

from app.research.analysis_preparation import canonical_bytes
from app.research.observation_context import contextualize
from scripts import review_milestone7_observations as runner


def observation():
    return dict(case_origin="hybrid", identity_resolution="resolved", relationship="current_owner",
                relationship_time="current_at_signal", operating_status="active", contradiction_state="none",
                supported_source_ids=["1"], contradictions=[], unresolved_questions=["Confirm timing"],
                summary="Fictional evidence supports an ownership clue.", state_fit="supported",
                private_company_fit="supported")


def context():
    return dict(reviewer="fixture reviewer", review_kind="agent_interpretation",
                operating_supported_on="2026-09-11", operating_source_ids=["1"],
                geography_basis="operating_presence", geography_state="CO", geography_source_ids=["1"])


def assess(output=None, **changes):
    ctx = context(); ctx.update(changes)
    return contextualize(output or observation(), {"1"}, "hybrid", as_of=date(2026, 9, 11),
                         requested_state="CO", context=ctx)


@pytest.mark.parametrize("supported,scope", [("2024-06-03", "historical"), (None, "undated")])
@pytest.mark.parametrize("status", ["active", "inactive"])
def test_old_or_undated_activity_preserves_clue_without_current_conclusion(supported, scope, status):
    output = observation(); output["operating_status"] = status
    result = assess(output, operating_supported_on=supported)
    assert result["model_observation"] == output
    assert result["temporal_scope"] == scope and result["operating_status_at_assessment"] == "unknown"
    assert result["deterministic_research_disposition"] == "needs_more_research"


def test_contemporaneous_supported_dimensions_allow_guidance_not_promotion():
    result = assess()
    assert result["operating_status_at_assessment"] == "active"
    assert result["deterministic_research_disposition"] == "candidate_supported"
    assert result["human_decision"] is None and result["promoted"] is False


@pytest.mark.parametrize("basis,state,fit", [
    ("dateline", "CO", "unknown"), ("address", "NC", "unknown"), ("address", "CO", "unknown"),
    ("legal_domicile", "CO", "unknown"), ("legal_domicile", "NC", "unknown"),
    ("operating_presence", "CO", "supported"), ("operating_presence", "NC", "unknown"),
    ("explicit_absence", "CO", "out_of_scope"), ("explicit_absence", "NC", "unknown"),
    ("unknown", None, "unknown"),
])
def test_geography_is_scoped_to_operating_presence(basis, state, fit):
    result = assess(geography_basis=basis, geography_state=state)
    assert result["requested_state_operating_fit"] == fit
    assert result["deterministic_research_disposition"] == (
        "candidate_supported" if fit == "supported" else "needs_more_research")


@pytest.mark.parametrize("changes", [
    {"operating_supported_on":"2026-09-12"}, {"operating_supported_on":"2026-02-30"},
    {"operating_supported_on":"20260911"}, {"operating_source_ids":[]},
    {"geography_source_ids":[]}, {"geography_source_ids":["private-invalid-id"]},
    {"geography_basis":"invented"}, {"geography_state":None}, {"reviewer":""},
])
def test_invalid_context_is_refused_without_exposing_values(changes):
    with pytest.raises(ValueError) as error:
        assess(**changes)
    assert "private-invalid-id" not in str(error.value)


def test_role_boundary_and_input_immutability():
    output = observation(); output["relationship"] = "non_owner_role"
    ctx = context(); before = deepcopy((output, ctx))
    result = contextualize(output, {"1"}, "hybrid", as_of=date(2026, 9, 11), requested_state="CO", context=ctx)
    assert result["deterministic_research_disposition"] == "no_qualifying_relationship"
    assert (output, ctx) == before
    result["model_observation"]["summary"] = "changed"
    result["review_context"]["operating_source_ids"].append("later")
    assert (output, ctx) == before


def test_invalid_model_observation_is_not_repaired_by_context():
    output = observation(); output["supported_source_ids"] = ["outside"]
    with pytest.raises(ValueError, match="Invalid model"):
        assess(output)


def test_offline_report_binds_inputs_and_preserves_original(tmp_path, monkeypatch):
    result = {"calls":[{"slot":"fixture", "model_observation":observation()}]}
    bundle = {"requests":[{"slot":"fixture", "request":{"input":json.dumps({
        "sources":[{"source_id":"1"}], "case_origin":"hybrid", "as_of":"2026-09-11", "requested_state":"CO"})}}]}
    raw, frozen = canonical_bytes(result), canonical_bytes(bundle)
    monkeypatch.setattr(runner, "RESULT_SHA256", sha256(raw).hexdigest())
    monkeypatch.setattr(runner, "BUNDLE_SHA256", sha256(frozen).hexdigest())
    monkeypatch.setattr(runner, "REVIEWS", {"fixture":("2024-06-03","1","address","NC")})
    report = runner.review(raw, frozen)
    row = report["reviews"][0]
    assert row["model_observation"] == result["calls"][0]["model_observation"]
    assert row["requested_state_operating_fit"] == "unknown"
    assert row["operating_status_at_assessment"] == "unknown"
    assert report["human_usefulness"] is None and report["external_calls"] == 0
    with pytest.raises(ValueError, match="Unreviewed"):
        runner.review(raw+b" ", frozen)
    with pytest.raises(ValueError, match="Unreviewed"):
        runner.review(raw, frozen+b" ")
