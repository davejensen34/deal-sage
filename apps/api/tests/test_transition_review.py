from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.domain.models import AuditEvent, CandidateMatch, ClaimContradiction, EvidenceClaim
from app.domain.transition_policies import transition_policy
from app.research.cases import ResearchCaseService
from app.research.proposal_dispositions import ModelProposalDispositionService
from app.research.review_queue import ResearchReviewQueueService, ReviewQueueSpec
from app.research.transitions import case_transitions
from test_review_queue import reviewable_case


FAMILIES = ["possible_death", "retirement", "succession", "ownership_change", "founder_exit", "dissolution", "restructuring", "leadership_change"]


def prepared(db, family="retirement"):
    case, business, evidence, owner, transition, proposal = reviewable_case(db)
    owner.object_value = {**owner.object_value, "registration_number": "UT-FICTIONAL-001"}
    transition.subject_type = transition_policy(family).subject_type
    transition.object_value = {
        "signal_type": family, "person": "Jordan Example", "business": "Fictional Business",
        "registration_number": "UT-FICTIONAL-001", "event_status": "planned", "event_date": "2027-01-01",
    }
    evidence.published_at = datetime(2026, 9, 1, tzinfo=timezone.utc)
    db.commit()
    ModelProposalDispositionService(db).add(proposal.id, analyst_name="Test Analyst", decision="accept", rationale="Review the source-linked event without assuming completed ownership change.")
    spec = ReviewQueueSpec(case.id, proposal.id, owner.id, transition.id, "Fictional Business", "Fictional Business", "UT", [])
    return case, owner, transition, proposal, spec


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("origin", ["signal_first", "business_first", "hybrid"])
def test_all_families_retain_scope_dates_and_unknown_current_ownership(override_db_session, family, origin):
    db = override_db_session
    case, owner, transition, proposal, spec = prepared(db, family)
    case.origin_strategy = origin
    db.commit()
    candidate = ResearchReviewQueueService(db).promote(spec, analyst_name="Test Analyst")
    assert candidate.signal.signal_type == family
    assert candidate.signal.possible_transition_date.isoformat() == "2027-01-01"
    assert candidate.signal.publication_date.isoformat() == "2026-09-01"
    assert candidate.relationship_record.relationship_type == "owner"
    assert candidate.relationship_record.active is None
    assert candidate.business.status == "unknown"
    assert candidate.status == "needs_review"
    assert "Event completion has not been established." in candidate.missing_evidence
    assert candidate.signal_identity_confidence == 29  # Existing deterministic arithmetic.
    assert "Utah legal entity" not in candidate.recommended_next_action
    audit = db.scalar(select(AuditEvent).where(AuditEvent.candidate_id == candidate.id))
    assert audit.after_state["signal_type"] == family
    assert audit.after_state["transition_claim_id"] == transition.id
    assert audit.after_state["event_status"] == "planned"
    assert ResearchReviewQueueService(db).promote(spec, analyst_name="Test Analyst").id == candidate.id


@pytest.mark.parametrize("failure", ["name_only", "cross_person", "cross_business", "cross_event_business", "cross_case_evidence", "unlinked_claim", "executive", "unknown_type", "cancelled", "conflict", "later_rejection", "stopped", "malformed_date", "entity_without_anchor"])
def test_unsupported_cases_remain_investigable_without_candidate(override_db_session, failure):
    db = override_db_session
    case, owner, transition, proposal, spec = prepared(db, "dissolution" if failure == "entity_without_anchor" else "retirement")
    if failure == "name_only":
        transition.evidence_id = proposal.supported_evidence_ids[0]
        transition.object_value = {"signal_type": "retirement", "person": "Jordan Example"}
    elif failure == "cross_person":
        transition.object_value = {**transition.object_value, "person": "Other Person"}
    elif failure == "cross_event_business":
        transition.object_value = {**transition.object_value, "business": "Other Business"}
    elif failure == "cross_business":
        owner.object_value = {**owner.object_value, "business": "Other Business"}
    elif failure == "cross_case_evidence":
        _, _, other_evidence, _, _, _ = reviewable_case(db)
        transition.evidence_id = other_evidence.id
    elif failure == "unlinked_claim":
        proposal.supported_claim_ids = [owner.id]
    elif failure == "executive":
        owner.relationship_semantics = "executive"
    elif failure == "unknown_type":
        transition.object_value = {**transition.object_value, "signal_type": "invented"}
    elif failure == "cancelled":
        transition.object_value = {**transition.object_value, "event_status": "cancelled"}
    elif failure == "conflict":
        db.add(ClaimContradiction(case_id=case.id, left_claim_id=owner.id, right_claim_id=transition.id, contradiction_type="identity", rationale="Conflicting retained identity", status="open"))
    elif failure == "later_rejection":
        ModelProposalDispositionService(db).add(proposal.id, analyst_name="Test Analyst", decision="reject", rationale="Later review invalidated the proposal.")
    elif failure == "stopped":
        case.status = "stopped"
    elif failure == "malformed_date":
        transition.object_value = {**transition.object_value, "event_date": "next year"}
    else:
        transition.object_value = {**transition.object_value, "registration_number": None}
    db.commit()
    before = db.scalar(select(CandidateMatch.id).order_by(CandidateMatch.id.desc()))
    with pytest.raises(ValueError):
        ResearchReviewQueueService(db).promote(spec, analyst_name="Test Analyst")
    db.rollback()
    assert case.candidate_match_id is None
    assert db.scalar(select(CandidateMatch.id).order_by(CandidateMatch.id.desc())) == before
    assert db.get(EvidenceClaim, transition.id) is not None
    # Invalid legacy fields still render as uncertainty instead of breaking reads.
    assert isinstance(case_transitions(db, case.id), list)


def test_legacy_mortality_is_readable_without_mutating_claim(client, override_db_session):
    db = override_db_session
    case, _, _, owner, transition, proposal = reviewable_case(db)
    original = dict(transition.object_value)
    response = client.get("/api/research/case-narratives")
    narrative = next(c for c in response.json()["cases"] if c["id"] == case.id)
    item = narrative["transitions"][0]
    assert item["signal_type"] == "possible_death"
    assert item["event_date"] is None
    assert item["event_status"] == "unknown"
    assert item["policy"]["ownership_limitations"]
    assert transition.object_value == original


@pytest.mark.parametrize("value", [
    {"signal_type": "dissolution"},
    {"signal_type": "retirement", "event_date": "yesterday"},
    {"signal_type": "retirement", "event_status": "definitely true"},
])
def test_typed_claim_structure_is_checked_before_persistence(override_db_session, value):
    db = override_db_session
    case, _, evidence, _, _, _ = reviewable_case(db)
    with pytest.raises(ValueError):
        ResearchCaseService(db).add_claim(case.id, evidence.id, subject_type="person", predicate="transition", object_value=value, confidence=0.5, classification="source_fact", source_authority="publisher", directness="direct")
