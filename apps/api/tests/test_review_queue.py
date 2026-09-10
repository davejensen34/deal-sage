import pytest
from sqlalchemy import select

from app.domain.models import AuditEvent, CandidateScoreAssessment, Evidence, ReviewCase, Source
from app.research.cases import ResearchCaseService
from app.research.model_proposals import ModelProposalService
from app.research.proposal_dispositions import ModelProposalDispositionService
from app.research.review_queue import ResearchReviewQueueService, ReviewQueueSpec


def reviewable_case(db):
    cases = ResearchCaseService(db)
    case = cases.create_case("business_first")
    business_evidence = cases.add_evidence(
        case.id,
        source_mode="case_specific_research",
        canonical_url="https://example.test/fictional-business",
        publisher="Fictional Business",
        source_type="business_website",
        content=b"Fictional business website.",
        relevant_excerpt="Fictional Business has offices in Utah.",
        extracted_facts={"operating_status": "active_public_website"},
        provenance={"provider": "fixture"},
    )
    obituary = cases.add_evidence(
        case.id,
        source_mode="case_specific_research",
        canonical_url="https://example.test/fictional-obituary",
        publisher="Fictional Memorial",
        source_type="obituary",
        content=b"Fictional obituary.",
        relevant_excerpt="Jordan Example was the owner of Fictional Business.",
        extracted_facts={"transition_signal": "reported_death"},
        provenance={"provider": "fixture"},
    )
    owner = cases.add_claim(
        case.id,
        obituary.id,
        subject_type="person_business_relationship",
        predicate="relationship",
        object_value={"person": "Jordan Example", "business": "Fictional Business"},
        relationship_semantics="owner",
        confidence=1,
        classification="source_fact",
        source_authority="publisher",
        directness="direct",
    )
    transition = cases.add_claim(
        case.id,
        obituary.id,
        subject_type="person",
        predicate="transition",
        object_value={"person": "Jordan Example", "event": "reported death"},
        confidence=1,
        classification="source_fact",
        source_authority="publisher",
        directness="document_context",
    )
    proposal = ModelProposalService(db).record(
        case.id,
        task="match_analysis",
        provider="fixture",
        model="fixture-v1",
        prompt_version="ambiguity-analysis-v1",
        schema_version="ambiguity-analysis-v1",
        execution_outcome="completed",
        proposed_output={"subject_name": "Jordan Example", "relationship": "former_owner"},
        supported_evidence_ids=[business_evidence.id, obituary.id],
        supported_claim_ids=[owner.id, transition.id],
    )
    return case, business_evidence, obituary, owner, transition, proposal


def test_only_accepted_same_subject_owner_case_enters_review_queue(override_db_session):
    case, _, _, owner, transition, proposal = reviewable_case(override_db_session)
    ModelProposalDispositionService(override_db_session).add(
        proposal.id,
        analyst_name="Test Analyst",
        decision="accept",
        rationale="The explicit owner statement is supported; current operation remains unresolved.",
    )

    candidate = ResearchReviewQueueService(override_db_session).promote(
        ReviewQueueSpec(
            case_id=case.id,
            accepted_proposal_id=proposal.id,
            owner_claim_id=owner.id,
            transition_claim_id=transition.id,
            business_label="Fictional Business Utah franchise",
            doing_business_as="Fictional Business",
            state="UT",
            missing_evidence=["Current owner"],
        ),
        analyst_name="Test Analyst",
    )

    assert candidate.status == "needs_review"
    assert candidate.owner_business_confidence == 60
    assert candidate.signal_identity_confidence == 29
    assert candidate.overall_candidate_confidence == 29
    assert case.candidate_match_id == candidate.id
    assert override_db_session.scalar(select(ReviewCase).where(ReviewCase.candidate_id == candidate.id)).status == "open"
    assert len(override_db_session.scalars(select(Evidence).where(Evidence.candidate_id == candidate.id)).all()) == 2
    score = override_db_session.scalar(select(CandidateScoreAssessment).where(CandidateScoreAssessment.candidate_id == candidate.id))
    assert score.provenance_classification == "evidence_derived"
    assert score.supporting_evidence_ids == [item.id for item in candidate.evidence]
    assert all(not source.is_demo for source in override_db_session.scalars(select(Source).where(Source.id.in_([item.source_id for item in candidate.evidence]))).all())
    assert override_db_session.scalar(select(AuditEvent).where(AuditEvent.candidate_id == candidate.id)).actor == "Test Analyst"


def test_unreviewed_proposal_cannot_enter_queue(override_db_session):
    case, _, _, owner, transition, proposal = reviewable_case(override_db_session)
    with pytest.raises(ValueError, match="accepted completed"):
        ResearchReviewQueueService(override_db_session).promote(
            ReviewQueueSpec(
                case_id=case.id,
                accepted_proposal_id=proposal.id,
                owner_claim_id=owner.id,
                transition_claim_id=transition.id,
                business_label="Fictional Business Utah franchise",
                doing_business_as="Fictional Business",
                state="UT",
                missing_evidence=[],
            ),
            analyst_name="Test Analyst",
        )
