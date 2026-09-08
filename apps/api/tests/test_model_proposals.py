import pytest

from app.research.cases import ResearchCaseService
from app.research.model_proposals import ModelProposalService


def case_lineage(db, suffix: str = "one"):
    cases = ResearchCaseService(db)
    case = cases.create_case("hybrid")
    evidence = cases.add_evidence(
        case.id,
        source_mode="case_specific_research",
        canonical_url=f"https://example.test/{suffix}",
        publisher="Example Publisher",
        source_type="business_profile",
        content=f"fictional evidence {suffix}".encode(),
        relevant_excerpt="Fictional Example Tool Works identifies a founder.",
        extracted_facts={"business_name": "Fictional Example Tool Works"},
        provenance={"provider": "fixture"},
    )
    claim = cases.add_claim(
        case.id,
        evidence.id,
        subject_type="person_business_relationship",
        predicate="relationship",
        object_value={"business_name": "Fictional Example Tool Works"},
        relationship_semantics="founder",
        confidence=0.8,
        classification="source_fact",
        source_authority="publisher",
        directness="direct_statement",
    )
    return case, evidence, claim


def test_completed_model_proposal_preserves_safe_output_and_provenance(override_db_session):
    case, evidence, claim = case_lineage(override_db_session)

    proposal = ModelProposalService(override_db_session).record(
        case.id,
        task="match_analysis",
        provider="fixture-provider",
        model="fixture-model-v1",
        prompt_version="match-v1",
        schema_version="proposal-v1",
        execution_outcome="completed",
        proposed_output={"match": "ambiguous", "summary": "A second non-name dimension is required."},
        supported_evidence_ids=[evidence.id],
        supported_claim_ids=[claim.id],
        input_tokens=120,
        output_tokens=30,
        total_tokens=150,
        latency_ms=45,
        cost_cents=2,
    )

    assert proposal.execution_outcome == "completed"
    assert proposal.supported_evidence_ids == [evidence.id]
    assert proposal.supported_claim_ids == [claim.id]
    assert proposal.proposed_output["match"] == "ambiguous"
    assert not hasattr(proposal, "updated_at")


def test_completed_proposal_requires_same_case_lineage(override_db_session):
    first, first_evidence, _ = case_lineage(override_db_session, "first")
    _, second_evidence, second_claim = case_lineage(override_db_session, "second")
    service = ModelProposalService(override_db_session)

    with pytest.raises(ValueError, match="same research case"):
        service.record(
            first.id,
            task="business_extraction",
            provider="fixture",
            model="fixture-v1",
            prompt_version="extract-v1",
            schema_version="proposal-v1",
            execution_outcome="completed",
            proposed_output={"business_name": "Fictional Example"},
            supported_evidence_ids=[second_evidence.id],
        )
    with pytest.raises(ValueError, match="same research case"):
        service.record(
            first.id,
            task="evidence_synthesis",
            provider="fixture",
            model="fixture-v1",
            prompt_version="synthesis-v1",
            schema_version="proposal-v1",
            execution_outcome="completed",
            proposed_output={"summary": "Fictional summary"},
            supported_evidence_ids=[first_evidence.id],
            supported_claim_ids=[second_claim.id],
        )


def test_non_completed_execution_keeps_only_safe_failure_metadata(override_db_session):
    case, _, _ = case_lineage(override_db_session)

    proposal = ModelProposalService(override_db_session).record(
        case.id,
        task="research_plan",
        provider="fixture-provider",
        model="fixture-model-v1",
        prompt_version="plan-v1",
        schema_version="proposal-v1",
        execution_outcome="refusal",
        input_tokens=40,
        total_tokens=40,
        latency_ms=12,
        error_class="AIProviderRefusalError",
    )

    assert proposal.proposed_output is None
    assert proposal.error_class == "AIProviderRefusalError"
    with pytest.raises(ValueError, match="cannot persist provider output"):
        ModelProposalService(override_db_session).record(
            case.id,
            task="research_plan",
            provider="fixture-provider",
            model="fixture-model-v1",
            prompt_version="plan-v1",
            schema_version="proposal-v1",
            execution_outcome="failed",
            proposed_output={"provider_body": "must not persist"},
            error_class="RuntimeError",
        )


def test_proposal_rejects_sensitive_fields_and_inconsistent_usage(override_db_session):
    case, evidence, _ = case_lineage(override_db_session)
    service = ModelProposalService(override_db_session)

    with pytest.raises(ValueError, match="Forbidden source field"):
        service.record(
            case.id,
            task="business_extraction",
            provider="fixture",
            model="fixture-v1",
            prompt_version="extract-v1",
            schema_version="proposal-v1",
            execution_outcome="completed",
            proposed_output={"session_token": "unsafe"},
            supported_evidence_ids=[evidence.id],
        )
    with pytest.raises(ValueError, match="Total tokens"):
        service.record(
            case.id,
            task="match_analysis",
            provider="fixture",
            model="fixture-v1",
            prompt_version="match-v1",
            schema_version="proposal-v1",
            execution_outcome="completed",
            proposed_output={"match": "unresolved"},
            supported_evidence_ids=[evidence.id],
            input_tokens=10,
            output_tokens=5,
            total_tokens=20,
        )
