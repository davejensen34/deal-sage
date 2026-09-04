import pytest

from app.research.cases import ResearchCaseService
from app.research.conclusions import AnalystConclusionService
from app.research.confidence import ConfidenceService


def case_claim(db, case_id, suffix, predicate, value, semantics=None):
    service = ResearchCaseService(db)
    evidence = service.add_evidence(
        case_id,
        source_mode="case_specific_research",
        canonical_url=f"https://example.test/narrative-{suffix}",
        publisher="Example Publisher",
        source_type="obituary",
        content=f"Narrative evidence {suffix}".encode(),
        relevant_excerpt=f"Narrative evidence {suffix}",
        extracted_facts={},
        provenance={},
    )
    return service.add_claim(
        case_id,
        evidence.id,
        subject_type="case",
        predicate=predicate,
        object_value={"value": value},
        relationship_semantics=semantics,
        confidence=1,
        classification="source_fact",
        source_authority="government",
        directness="direct_statement",
    )


def test_analyst_conclusion_is_distinct_and_case_local(override_db_session):
    service = ResearchCaseService(override_db_session)
    first = service.create_case("signal_first")
    second = service.create_case("business_first")
    claim = case_claim(override_db_session, first.id, "relationship", "relationship", "Example", "owner")
    inference = service.add_inference(
        first.id,
        inference_type="opportunity_hypothesis",
        statement="The evidence supports analyst review.",
        supporting_claim_ids=[claim.id],
        confidence=0.7,
        method="deterministic",
    )
    conclusion = AnalystConclusionService(override_db_session).add(
        first.id,
        analyst_name="Demo Analyst",
        outcome="partially_supported",
        statement="Ownership needs one more independent source.",
        supporting_inference_ids=[inference.id],
        status="final",
    )
    assert conclusion.outcome == "partially_supported"
    assert inference.status == "proposed"
    with pytest.raises(ValueError, match="same research case"):
        AnalystConclusionService(override_db_session).add(
            second.id,
            analyst_name="Demo Analyst",
            outcome="supported",
            statement="Wrong case.",
            supporting_inference_ids=[inference.id],
        )


def test_case_narrative_exposes_layers_without_raw_content(client, override_db_session):
    service = ResearchCaseService(override_db_session)
    case = service.create_case("hybrid")
    legal = case_claim(override_db_session, case.id, "legal", "legal_name", "Example LLC")
    relationship = case_claim(
        override_db_session, case.id, "owner", "relationship", "Example LLC", "owner"
    )
    transition = case_claim(
        override_db_session, case.id, "transition", "transition_name", "Jordan Lee"
    )
    ConfidenceService(override_db_session).assess(case.id)
    inference = service.add_inference(
        case.id,
        inference_type="opportunity_hypothesis",
        statement="Reviewable but incomplete.",
        supporting_claim_ids=[legal.id, relationship.id, transition.id],
        confidence=0.5,
        method="deterministic",
    )
    AnalystConclusionService(override_db_session).add(
        case.id,
        analyst_name="Demo Analyst",
        outcome="needs_more_research",
        statement="Business identity needs a registration identifier.",
        supporting_inference_ids=[inference.id],
    )

    response = client.get("/api/research/case-narratives")
    assert response.status_code == 200
    narrative = next(item for item in response.json()["cases"] if item["id"] == case.id)
    assert narrative["origin_strategy"] == "hybrid"
    assert narrative["confidence"]["owner_relationship"] == 75
    assert narrative["conclusion"]["outcome"] == "needs_more_research"
    assert "content" not in narrative["evidence"][0]
