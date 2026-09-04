import pytest

from app.research.cases import ResearchCaseService


def evidence_for(service: ResearchCaseService, case_id: int, suffix: str = "one"):
    return service.add_evidence(
        case_id,
        source_mode="case_specific_research",
        canonical_url=f"https://example.test/{suffix}",
        publisher="Example Publisher",
        source_type="obituary",
        content=f"public source content {suffix}".encode(),
        relevant_excerpt="Founded Example Tool Works.",
        extracted_facts={"business_clue": "Example Tool Works"},
        provenance={"query": "bounded example query", "search_provider": "fixture"},
    )


def test_case_can_begin_without_a_person_or_business(override_db_session):
    service = ResearchCaseService(override_db_session)
    case = service.create_case("signal_first")

    assert case.person_id is None
    assert case.business_id is None
    assert case.research_budget["max_documents"] == 10
    with pytest.raises(ValueError, match="origin strategy"):
        service.create_case("obituary_only")


def test_minimal_evidence_claim_and_inference_remain_distinct(override_db_session):
    service = ResearchCaseService(override_db_session)
    case = service.create_case("signal_first")
    evidence = evidence_for(service, case.id)
    claim = service.add_claim(
        case.id,
        evidence.id,
        subject_type="person_business_relationship",
        predicate="relationship",
        object_value={"business_name": "Example Tool Works"},
        relationship_semantics="founder",
        confidence=0.9,
        classification="source_fact",
        source_authority="self_published",
        directness="direct_statement",
    )
    inference = service.add_inference(
        case.id,
        inference_type="candidate_business_match",
        statement="The named business may resolve to an official entity.",
        supporting_claim_ids=[claim.id],
        confidence=0.6,
        method="deterministic",
    )

    assert len(evidence.content_hash) == 64
    assert not hasattr(evidence, "content")
    assert claim.relationship_semantics == "founder"
    assert inference.supporting_claim_ids == [claim.id]
    assert inference.method == "deterministic"


def test_relationship_language_and_model_provenance_are_validated(override_db_session):
    service = ResearchCaseService(override_db_session)
    case = service.create_case("hybrid")
    evidence = evidence_for(service, case.id)
    with pytest.raises(ValueError, match="precise supported semantics"):
        service.add_claim(
            case.id,
            evidence.id,
            subject_type="relationship",
            predicate="relationship",
            object_value={"business_name": "Example"},
            relationship_semantics="business_person",
            confidence=0.5,
            classification="source_fact",
            source_authority="unknown",
            directness="indirect",
        )
    claim = service.add_claim(
        case.id,
        evidence.id,
        subject_type="relationship",
        predicate="relationship",
        object_value={"business_name": "Example"},
        relationship_semantics="employee",
        confidence=0.7,
        classification="source_fact",
        source_authority="publisher",
        directness="direct_statement",
    )
    with pytest.raises(ValueError, match="provider, model, and prompt"):
        service.add_inference(
            case.id,
            inference_type="relationship_analysis",
            statement="Employment does not establish ownership.",
            supporting_claim_ids=[claim.id],
            confidence=0.9,
            method="model_assisted",
        )


def test_cross_case_lineage_is_rejected(override_db_session):
    service = ResearchCaseService(override_db_session)
    first = service.create_case("signal_first")
    second = service.create_case("business_first")
    first_evidence = evidence_for(service, first.id, "first")
    with pytest.raises(ValueError, match="same research case"):
        service.add_claim(
            second.id,
            first_evidence.id,
            subject_type="business",
            predicate="legal_name",
            object_value={"value": "Example"},
            confidence=0.8,
            classification="source_fact",
            source_authority="publisher",
            directness="direct_statement",
        )


def test_persistent_connector_requires_an_evaluated_known_source(override_db_session):
    service = ResearchCaseService(override_db_session)
    case = service.create_case("business_first")
    with pytest.raises(ValueError, match="requires a known source"):
        service.add_evidence(
            case.id,
            source_mode="persistent_connector",
            canonical_url="https://example.test/connector",
            publisher="Example Publisher",
            source_type="government",
            content=b"bounded response",
            relevant_excerpt=None,
            extracted_facts={},
            provenance={"adapter": "example-v1"},
        )


def test_case_metrics_are_aggregate_only(client, override_db_session):
    service = ResearchCaseService(override_db_session)
    case = service.create_case("business_first")
    evidence_for(service, case.id, "private-case-value")

    response = client.get("/api/research/case-metrics")
    assert response.status_code == 200
    assert response.json()["cases"] >= 1
    assert response.json()["by_origin_strategy"]["business_first"] >= 1
    assert "private-case-value" not in str(response.json())
