from app.research.cases import ResearchCaseService
from app.research.confidence import ConfidenceService
from app.research.identity_resolution import IdentityResolutionService


def claim(db, case_id, suffix, predicate, value, *, semantics=None, authority="government", content=None):
    cases = ResearchCaseService(db)
    text = content or f"Evidence {suffix}"
    evidence = cases.add_evidence(
        case_id, source_mode="case_specific_research",
        canonical_url=f"https://example.test/{suffix}", publisher=f"Publisher {suffix}",
        source_type="government", content=text.encode(), relevant_excerpt=text,
        extracted_facts={}, provenance={},
    )
    result = cases.add_claim(
        case_id, evidence.id, subject_type="case", predicate=predicate,
        object_value={"value": value}, relationship_semantics=semantics,
        confidence=1, classification="source_fact", source_authority=authority,
        directness="direct_statement",
    )
    return evidence, result


def complete_case(db):
    case = ResearchCaseService(db).create_case("hybrid")
    claims = [
        claim(db, case.id, "name", "legal_name", "Summit Works")[1],
        claim(db, case.id, "registration", "registration_number", "CO-123")[1],
        claim(db, case.id, "owner", "relationship", "Summit Works", semantics="owner")[1],
        claim(db, case.id, "death-name", "transition_name", "Jordan Lee", authority="publisher")[1],
        claim(db, case.id, "death-date", "transition_date", "2026-01-02", authority="publisher")[1],
        claim(db, case.id, "death-place", "transition_geography", "CO", authority="publisher")[1],
        claim(db, case.id, "status", "operating_status", "active")[1],
    ]
    return case, claims


def test_confidence_axes_are_separate_reproducible_and_explained(override_db_session):
    case, claims = complete_case(override_db_session)
    result = ConfidenceService(override_db_session).assess(case.id)
    assert result.business_identity == 75
    assert result.owner_relationship == 75
    assert result.transition_identity == 68
    assert result.operating_status == 60
    assert result.overall_opportunity == 68
    assert result.supporting_claim_ids == [claim.id for claim in claims]
    assert all("impact" in factor for factor in result.factors)
    assert case.confidence["assessment_id"] == result.id


def test_duplicate_evidence_does_not_multiply_support(override_db_session):
    case = ResearchCaseService(override_db_session).create_case("business_first")
    first_evidence, first = claim(override_db_session, case.id, "one", "registration_number", "CO-1", content="copied")
    second_evidence, second = claim(override_db_session, case.id, "two", "registration_number", "CO-1", content="copied")
    IdentityResolutionService(override_db_session).classify_evidence_pair(
        case.id, first_evidence.id, second_evidence.id
    )
    result = ConfidenceService(override_db_session).assess(case.id)
    factors = [factor for factor in result.factors if factor["feature"] == "registration_number"]
    assert len(factors) == 2
    assert sum(factor["impact"] for factor in factors) == 45
    assert any(
        factor.get("suppressed_reason") == "non_independent_evidence"
        for factor in factors
    )
    assert result.business_identity == 45
    assert set(result.supporting_claim_ids).issubset({first.id, second.id})


def test_former_owner_and_inactive_business_cap_opportunity(override_db_session):
    case, _ = complete_case(override_db_session)
    claim(override_db_session, case.id, "former", "relationship", "Summit Works", semantics="former_owner", authority="publisher")
    claim(override_db_session, case.id, "inactive", "operating_status", "inactive")
    result = ConfidenceService(override_db_session).assess(case.id)
    assert result.owner_relationship < 75
    assert result.operating_status == 0
    assert result.overall_opportunity <= 10


def test_open_contradiction_penalizes_only_relevant_axis(override_db_session):
    case, claims = complete_case(override_db_session)
    former = claim(override_db_session, case.id, "conflict", "relationship", "Summit Works", semantics="former_owner")[1]
    IdentityResolutionService(override_db_session).record_contradiction(
        case.id, claims[2].id, former.id, contradiction_type="relationship",
        rationale="Current and former ownership claims conflict.",
    )
    result = ConfidenceService(override_db_session).assess(case.id)
    assert result.owner_relationship == 5
    assert result.business_identity == 75
    assert set(result.contradictory_claim_ids) == {claims[2].id, former.id}


def test_ambiguous_identity_keeps_overall_at_zero(override_db_session):
    case = ResearchCaseService(override_db_session).create_case("signal_first")
    claim(override_db_session, case.id, "possible-owner", "relationship", "Example", semantics="owner")
    result = ConfidenceService(override_db_session).assess(case.id)
    assert result.owner_relationship == 75
    assert result.business_identity == 0
    assert result.transition_identity == 0
    assert result.overall_opportunity == 0


def test_profile_estimates_remain_labeled_and_claim_backed(override_db_session):
    case = ResearchCaseService(override_db_session).create_case("business_first")
    _, estimate = claim(
        override_db_session, case.id, "estimate", "employee_range", "11-50", authority="publisher"
    )
    observation = ConfidenceService(override_db_session).add_profile_observation(
        case.id, field_name="employee_range", value={"range": "11-50"},
        classification="third_party_estimate", confidence=0.6,
        supporting_claim_ids=[estimate.id],
    )
    assert observation.classification == "third_party_estimate"
    assert observation.supporting_claim_ids == [estimate.id]

    inference = ResearchCaseService(override_db_session).add_inference(
        case.id,
        inference_type="estimated_revenue_range",
        statement="Available public clues suggest a broad revenue range.",
        supporting_claim_ids=[estimate.id],
        confidence=0.4,
        method="deterministic",
    )
    inferred = ConfidenceService(override_db_session).add_profile_observation(
        case.id,
        field_name="revenue_range",
        value={"range": "$1M-$5M"},
        classification="dealsage_inference",
        confidence=0.4,
        inference_id=inference.id,
    )
    assert inferred.inference_id == inference.id
    assert inferred.supporting_claim_ids == []
