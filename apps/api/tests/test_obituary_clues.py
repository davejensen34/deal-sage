import pytest

from app.research.cases import ResearchCaseService
from app.research.obituary_clues import (
    BusinessClue,
    BusinessClueExtractor,
    DeterministicBusinessClueExtractor,
    ObituaryClueService,
)


TEXT = (
    "Jordan Lee founded Summit Tool Works in 1984. "
    "Later, Jordan was president of Western Supply. "
    "Jordan worked for Valley Metals. "
    "Jordan was the former owner of Canyon Fabrication. "
    "Jordan sold Canyon Fabrication in 2018. "
    "Jordan retired from Western Supply in 2020. "
    "Jordan helped run the family business, Lee Machine Shop, and the children continued it."
)


def add_obituary_evidence(db, *, source_type="obituary", excerpt=TEXT):
    cases = ResearchCaseService(db)
    case = cases.create_case("signal_first")
    evidence = cases.add_evidence(
        case.id,
        source_mode="case_specific_research",
        canonical_url="https://example.test/jordan-lee",
        publisher="Example Memorial",
        source_type=source_type,
        content=excerpt.encode(),
        relevant_excerpt=excerpt,
        extracted_facts={},
        provenance={"search_provider": "fixture"},
    )
    return case, evidence


@pytest.mark.asyncio
async def test_relationship_phrases_remain_semantically_distinct(override_db_session):
    case, evidence = add_obituary_evidence(override_db_session)
    claims = await ObituaryClueService(override_db_session).extract_claims(
        case.id,
        evidence.id,
        DeterministicBusinessClueExtractor(),
        source_authority="publisher",
    )

    relationships = {(claim.relationship_semantics, claim.object_value["business_name"]) for claim in claims}
    assert ("founder", "Summit Tool Works") in relationships
    assert ("executive", "Western Supply") in relationships
    assert ("employee", "Valley Metals") in relationships
    assert ("former_owner", "Canyon Fabrication") in relationships
    assert ("sold_business", "Canyon Fabrication") in relationships
    assert ("retired", "Western Supply") in relationships
    assert ("family_business_participant", "Lee Machine Shop") in relationships
    assert ("owner", "Canyon Fabrication") not in relationships
    assert all(claim.object_value["supporting_excerpt"] in TEXT for claim in claims)


@pytest.mark.asyncio
async def test_employment_and_executive_language_never_becomes_owner(override_db_session):
    text = "Avery Morgan worked at Northstar Motors. Avery was CEO of Harbor Logistics."
    case, evidence = add_obituary_evidence(override_db_session, excerpt=text)
    claims = await ObituaryClueService(override_db_session).extract_claims(
        case.id, evidence.id, DeterministicBusinessClueExtractor(), source_authority="publisher"
    )

    assert [claim.relationship_semantics for claim in claims] == ["employee", "executive"]
    assert not any(claim.relationship_semantics in {"owner", "co_owner"} for claim in claims)


@pytest.mark.asyncio
async def test_generic_or_ambiguous_business_reference_is_not_promoted(override_db_session):
    text = "Riley cherished the family business and later sold it."
    case, evidence = add_obituary_evidence(override_db_session, excerpt=text)
    claims = await ObituaryClueService(override_db_session).extract_claims(
        case.id, evidence.id, DeterministicBusinessClueExtractor(), source_authority="publisher"
    )
    assert claims == []


class UnsafeExtractor(BusinessClueExtractor):
    key = "unsafe-fixture"

    async def extract(self, text: str) -> list[BusinessClue]:
        return [
            BusinessClue(
                business_name="Example LLC",
                relationship_semantics="owner",
                relevant_excerpt=text,
                confidence=0.8,
                geography={"session_token": "must-not-persist"},
            )
        ]


@pytest.mark.asyncio
async def test_model_shaped_clues_are_validated_before_persistence(override_db_session):
    case, evidence = add_obituary_evidence(
        override_db_session, excerpt="Taylor was owner of Example LLC."
    )
    with pytest.raises(ValueError, match="Forbidden source field"):
        await ObituaryClueService(override_db_session).extract_claims(
            case.id, evidence.id, UnsafeExtractor(), source_authority="publisher"
        )


@pytest.mark.asyncio
async def test_extraction_rejects_non_obituary_evidence(override_db_session):
    case, evidence = add_obituary_evidence(
        override_db_session, source_type="government", excerpt="Taylor owned Example LLC."
    )
    with pytest.raises(ValueError, match="obituary-like"):
        await ObituaryClueService(override_db_session).extract_claims(
            case.id,
            evidence.id,
            DeterministicBusinessClueExtractor(),
            source_authority="government",
        )


class IncompleteModelExtractor(BusinessClueExtractor):
    key = "model-fixture"
    provider = "example-model-provider"

    async def extract(self, text: str) -> list[BusinessClue]:
        return []


@pytest.mark.asyncio
async def test_model_extractor_requires_complete_provenance(override_db_session):
    case, evidence = add_obituary_evidence(override_db_session)
    with pytest.raises(ValueError, match="provider, model, and prompt version"):
        await ObituaryClueService(override_db_session).extract_claims(
            case.id, evidence.id, IncompleteModelExtractor(), source_authority="publisher"
        )
