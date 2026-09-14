from copy import deepcopy
import json

import pytest

from app.research.analysis_preparation import observation_errors, INSTRUCTIONS as FROZEN_INSTRUCTIONS
from app.research.observation_contract import assess_observation, safe_diagnostic_codes, INSTRUCTIONS


def observation():
    return dict(case_origin="hybrid", identity_resolution="resolved", relationship="non_owner_role",
                relationship_time="current_at_signal", operating_status="unknown", contradiction_state="none",
                supported_source_ids=["source-1"], contradictions=[], unresolved_questions=["Verify ownership"],
                summary="Fictional executive retirement is a useful lead, not proof of ownership.",
                state_fit="supported", private_company_fit="supported")


def test_disposition_seam_is_reproducible_without_recovering_historical_outputs():
    output = observation()
    # Plausible research guidance can disagree with an undisclosed code label.
    old = {**output, "research_disposition": "needs_more_research"}
    assert observation_errors(old, {"source-1"}) == ["research_disposition_conflicts_with_target_dimensions"]
    new = assess_observation(output, {"source-1"}, "hybrid")
    assert new.diagnostic_codes == [] and new.model_observation == output
    assert new.deterministic_research_disposition == "no_qualifying_relationship"
    assert "research_disposition" not in new.model_observation
    assert "deterministic code" in INSTRUCTIONS
    assert "Do not choose a research disposition" not in FROZEN_INSTRUCTIONS


@pytest.mark.parametrize("fit", ["unknown", "out_of_scope", "supported"])
def test_target_fit_does_not_erase_useful_observations(fit):
    output = observation()
    output.update(relationship="current_owner", operating_status="active", state_fit=fit)
    result = assess_observation(output, {"source-1"}, "hybrid")
    assert result.model_observation == output
    assert result.deterministic_research_disposition == (
        "candidate_supported" if fit == "supported" else "needs_more_research")


@pytest.mark.parametrize("changes,code", [
    ({"relationship":"unclear"}, "relationship_time_conflicts_with_relationship"),
    ({"contradiction_state":"unresolved"}, "contradiction_state_requires_detail"),
    ({"supported_source_ids":["secret-token:DO-NOT-RETAIN"]}, "unsupported_source_ids"),
    ({"case_origin":"business_first"}, "case_origin_mismatch"),
    ({"research_disposition":"candidate_supported"}, "observation_schema"),
])
def test_semantic_and_schema_failures_retain_codes_only(changes, code):
    output = observation(); output.update(changes)
    result = assess_observation(output, {"source-1"}, "hybrid")
    assert result.model_observation is None and result.deterministic_research_disposition is None
    assert code in result.diagnostic_codes
    assert "DO-NOT-RETAIN" not in json.dumps(result.diagnostic_codes)


def test_unknown_errors_and_citation_details_cannot_escape_as_diagnostics():
    assert safe_diagnostic_codes(["unknown private detail", "unsupported_source_ids:private-id",
                                  "unsupported_source_ids:another-id"]) == [
                                      "unclassified_consistency_error", "unsupported_source_ids"]


def test_assessment_does_not_mutate_input_or_alias_retained_observation():
    output = observation(); before = deepcopy(output)
    result = assess_observation(output, {"source-1"}, "hybrid")
    assert output == before
    output["unresolved_questions"].append("later change")
    assert result.model_observation == before


def test_unknown_ownership_retains_the_clue_for_more_research():
    output = observation()
    output.update(relationship="unclear", relationship_time="unclear", identity_resolution="ambiguous")
    result = assess_observation(output, {"source-1"}, "hybrid")
    assert result.model_observation == output
    assert result.deterministic_research_disposition == "needs_more_research"
