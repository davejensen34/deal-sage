"""Offline contextual review; source assertions and model output are not truth."""

from copy import deepcopy
from datetime import date
import re

from app.research.observation_contract import assess_observation


VERSION = "m7-observation-context-v1"
BASES = {"operating_presence", "legal_domicile", "address", "dateline", "explicit_absence", "unknown"}


def contextualize(observation: dict, source_ids: set[str], case_origin: str, *,
                  as_of: date, requested_state: str, context: dict) -> dict:
    """Apply separately attributed context without rewriting a model observation.

    Context is a reviewer's interpretation of cited evidence, not an automatic
    extraction or human acceptance. The supported date describes the operating
    assertion, never merely retrieval time or a promised future event. No TTL is
    invented: earlier evidence is historical, not proof of closure or continuity.
    Requested-state fit here means operating presence, not legal domicile.
    """
    expected = {"reviewer", "review_kind", "operating_supported_on",
                "operating_source_ids", "geography_basis", "geography_state",
                "geography_source_ids"}
    if set(context) != expected or context["review_kind"] not in {"agent_interpretation", "human_interpretation"}:
        raise ValueError("Invalid review context")
    if not isinstance(context["reviewer"], str) or not context["reviewer"].strip():
        raise ValueError("Missing review attribution")
    if not re.fullmatch(r"[A-Z]{2}", requested_state):
        raise ValueError("Invalid requested state")
    basis, state = context["geography_basis"], context["geography_state"]
    if basis not in BASES or (state is not None and (not isinstance(state, str) or not re.fullmatch(r"[A-Z]{2}", state))):
        raise ValueError("Invalid geography context")
    if (basis == "unknown") != (state is None):
        raise ValueError("Geography basis requires its subject state")
    for field in ("operating_source_ids", "geography_source_ids"):
        ids = context[field]
        if not isinstance(ids, list) or any(not isinstance(i, str) or i not in source_ids for i in ids):
            raise ValueError("Unsupported context citation")
    supported = context["operating_supported_on"]
    if supported is not None:
        if not isinstance(supported, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", supported):
            raise ValueError("Invalid supported date")
        supported = date.fromisoformat(supported)
        if supported > as_of or not context["operating_source_ids"]:
            raise ValueError("Future or uncited operating assertion")
    if basis != "unknown" and not context["geography_source_ids"]:
        raise ValueError("Uncited geography assertion")
    original = assess_observation(observation, source_ids, case_origin)
    if original.diagnostic_codes:
        raise ValueError("Invalid model observation")

    temporal = "undated" if supported is None else "at_assessment" if supported == as_of else "historical"
    operating = observation["operating_status"] if temporal == "at_assessment" else "unknown"
    # An outside address/domicile is not evidence of no operating presence.
    fit = "unknown"
    if state == requested_state:
        if basis == "operating_presence":
            fit = "supported"
        elif basis == "explicit_absence":
            fit = "out_of_scope"
    effective = deepcopy(observation)
    effective.update(operating_status=operating, state_fit=fit)
    assessed = assess_observation(effective, source_ids, case_origin)
    if assessed.diagnostic_codes:
        raise ValueError("Invalid contextual assessment")
    return {"version": VERSION, "as_of": as_of.isoformat(), "requested_state": requested_state,
            "model_observation": deepcopy(observation), "review_context": deepcopy(context),
            "temporal_scope": temporal, "operating_status_at_assessment": operating,
            "requested_state_operating_fit": fit,
            "deterministic_research_disposition": assessed.deterministic_research_disposition,
            "human_decision": None, "promoted": False}
