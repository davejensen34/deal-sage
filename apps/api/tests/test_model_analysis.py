import pytest

from app.ai.providers.base import AIProvider, AIProviderRefusalError, TokenUsage
from app.domain.models import ResearchFrontierItem
from app.research.cases import ResearchCaseService
from app.research.model_analysis import ModelAnalysisService
from app.research.plan_approval import ResearchPlanApprovalService


class FixtureProvider(AIProvider):
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.last_usage = TokenUsage(input_tokens=80, output_tokens=20, total_tokens=100)

    async def extract_structured(self, text, schema):
        assert "Evidence packet" in text
        if self.error:
            raise self.error
        return self.output

    async def summarize(self, context):
        raise NotImplementedError

    async def analyze_match(self, context):
        raise NotImplementedError


def case_with_claim(db, semantics="owner"):
    cases = ResearchCaseService(db)
    case = cases.create_case("hybrid")
    evidence = cases.add_evidence(
        case.id,
        source_mode="case_specific_research",
        canonical_url="https://example.test/fictional-profile",
        publisher="Fictional Publisher",
        source_type="business_profile",
        content=b"Fictional owner and business profile.",
        relevant_excerpt="Jordan Example is identified as owner of Fictional Example Tool Works.",
        extracted_facts={"business_name": "Fictional Example Tool Works"},
        provenance={"provider": "fixture"},
    )
    claim = cases.add_claim(
        case.id,
        evidence.id,
        subject_type="person_business_relationship",
        predicate="relationship",
        object_value={"person": "Jordan Example", "business_name": "Fictional Example Tool Works"},
        relationship_semantics=semantics,
        confidence=0.8,
        classification="source_fact",
        source_authority="publisher",
        directness="direct_statement",
    )
    return case, evidence, claim


@pytest.mark.asyncio
async def test_business_extraction_persists_only_cited_observations(override_db_session):
    case, evidence, claim = case_with_claim(override_db_session)
    provider = FixtureProvider(
        {
            "observations": [
                {
                    "field": "legal_name",
                    "value": "Fictional Example Tool Works",
                    "evidence_ids": [evidence.id],
                    "claim_ids": [claim.id],
                }
            ],
            "unresolved_questions": ["Is the filing current?"],
            "summary": "The supplied evidence names a business.",
        }
    )

    proposal = await ModelAnalysisService(override_db_session).extract_business(
        case.id,
        provider,
        provider_name="fixture",
        model="fixture-v1",
        evidence_ids=[evidence.id],
        claim_ids=[claim.id],
    )

    assert proposal.execution_outcome == "completed"
    assert proposal.proposed_output["observations"][0]["field"] == "legal_name"
    assert proposal.total_tokens == 100


@pytest.mark.asyncio
async def test_research_plan_requires_approval_before_it_enters_frontier(override_db_session):
    case, evidence, claim = case_with_claim(override_db_session)
    provider = FixtureProvider(
        {
            "question_type": "verify_operating_status",
            "question": "Is the fictional business currently operating?",
            "rationale": "The supplied profile does not establish current status.",
            "next_action": "search",
            "query": "Fictional Example Tool Works current operating status",
            "source_type": "government",
            "evidence_ids": [evidence.id],
            "claim_ids": [claim.id],
            "expected_information_gain": "A current filing could resolve operating status.",
        }
    )

    proposal = await ModelAnalysisService(override_db_session).propose_research_plan(
        case.id,
        provider,
        provider_name="fixture",
        model="fixture-v1",
        evidence_ids=[evidence.id],
        claim_ids=[claim.id],
    )

    assert proposal.execution_outcome == "completed"
    assert proposal.proposed_output["next_action"] == "search"
    assert override_db_session.query(ResearchFrontierItem).count() == 0

    item = ResearchPlanApprovalService(override_db_session).approve(proposal.id, priority=70)
    assert item is not None
    assert item.proposal_id == proposal.id
    assert item.supporting_claim_ids == [claim.id]

    with pytest.raises(ValueError, match="already been approved"):
        ResearchPlanApprovalService(override_db_session).approve(proposal.id, priority=70)


@pytest.mark.asyncio
async def test_invalid_research_query_is_not_persisted_as_output(override_db_session):
    case, evidence, claim = case_with_claim(override_db_session)
    provider = FixtureProvider(
        {
            "question_type": "find_independent_evidence",
            "question": "Find independent support.",
            "rationale": "One source is insufficient.",
            "next_action": "search",
            "query": None,
            "source_type": "government",
            "evidence_ids": [evidence.id],
            "claim_ids": [claim.id],
            "expected_information_gain": "Independent support.",
        }
    )

    proposal = await ModelAnalysisService(override_db_session).propose_research_plan(
        case.id,
        provider,
        provider_name="fixture",
        model="fixture-v1",
        evidence_ids=[evidence.id],
        claim_ids=[claim.id],
    )

    assert proposal.execution_outcome == "invalid"
    assert proposal.proposed_output is None


@pytest.mark.asyncio
async def test_unsupported_business_citation_is_recorded_as_invalid_without_payload(override_db_session):
    case, evidence, claim = case_with_claim(override_db_session)
    provider = FixtureProvider(
        {
            "observations": [
                {
                    "field": "industry",
                    "value": "Manufacturing",
                    "evidence_ids": [999999],
                    "claim_ids": [claim.id],
                }
            ],
            "unresolved_questions": [],
            "summary": "Unsupported observation.",
        }
    )

    proposal = await ModelAnalysisService(override_db_session).extract_business(
        case.id,
        provider,
        provider_name="fixture",
        model="fixture-v1",
        evidence_ids=[evidence.id],
        claim_ids=[claim.id],
    )

    assert proposal.execution_outcome == "invalid"
    assert proposal.proposed_output is None
    assert proposal.error_class == "ValueError"


@pytest.mark.asyncio
async def test_ambiguity_analysis_requires_non_name_support_for_resolution(override_db_session):
    case, evidence, claim = case_with_claim(override_db_session)
    provider = FixtureProvider(
        {
            "subject_name": "Jordan Example",
            "identity_status": "resolved",
            "relationship": "current_owner",
            "relationship_time": "current_at_signal",
            "operating_status": "active",
            "support_dimensions": [],
            "evidence_ids": [evidence.id],
            "claim_ids": [claim.id],
            "contradictions": [],
            "unresolved_questions": [],
            "summary": "The name alone appears to match.",
        }
    )

    proposal = await ModelAnalysisService(override_db_session).analyze_ambiguity(
        case.id,
        provider,
        provider_name="fixture",
        model="fixture-v1",
        evidence_ids=[evidence.id],
        claim_ids=[claim.id],
    )

    assert proposal.execution_outcome == "invalid"
    assert proposal.proposed_output is None


@pytest.mark.asyncio
async def test_registered_agent_claim_cannot_be_promoted_to_owner(override_db_session):
    case, evidence, claim = case_with_claim(override_db_session, "registered_agent")
    provider = FixtureProvider(
        {
            "subject_name": "Jordan Example",
            "identity_status": "resolved",
            "relationship": "current_owner",
            "relationship_time": "current_at_signal",
            "operating_status": "active",
            "support_dimensions": ["relationship", "registration"],
            "evidence_ids": [evidence.id],
            "claim_ids": [claim.id],
            "contradictions": [],
            "unresolved_questions": [],
            "summary": "The registered agent is the owner.",
        }
    )

    proposal = await ModelAnalysisService(override_db_session).analyze_ambiguity(
        case.id,
        provider,
        provider_name="fixture",
        model="fixture-v1",
        evidence_ids=[evidence.id],
        claim_ids=[claim.id],
    )

    assert proposal.execution_outcome == "invalid"
    assert proposal.proposed_output is None


@pytest.mark.asyncio
async def test_owner_claim_for_another_person_cannot_support_transition_subject(override_db_session):
    case, evidence, claim = case_with_claim(override_db_session)
    claim.object_value = {"person": "Different Person", "business_name": "Fictional Example Tool Works"}
    override_db_session.commit()
    provider = FixtureProvider(
        {
            "subject_name": "Jordan Example",
            "identity_status": "resolved",
            "relationship": "former_owner",
            "relationship_time": "ended_at_signal",
            "operating_status": "active",
            "support_dimensions": ["relationship", "timeline"],
            "evidence_ids": [evidence.id],
            "claim_ids": [claim.id],
            "contradictions": [],
            "unresolved_questions": [],
            "summary": "An unrelated owner claim was cited for the transition subject.",
        }
    )

    proposal = await ModelAnalysisService(override_db_session).analyze_ambiguity(
        case.id,
        provider,
        provider_name="fixture",
        model="fixture-v1",
        evidence_ids=[evidence.id],
        claim_ids=[claim.id],
    )

    assert proposal.execution_outcome == "invalid"
    assert proposal.proposed_output is None
    assert proposal.error_class == "ValueError"


@pytest.mark.asyncio
async def test_relationship_timeline_conflict_is_not_persisted_as_a_proposal(override_db_session):
    case, evidence, claim = case_with_claim(override_db_session)
    provider = FixtureProvider(
        {
            "subject_name": "Jordan Example",
            "identity_status": "resolved",
            "relationship": "former_owner",
            "relationship_time": "current_at_signal",
            "operating_status": "active",
            "support_dimensions": ["relationship", "timeline"],
            "evidence_ids": [evidence.id],
            "claim_ids": [claim.id],
            "contradictions": [],
            "unresolved_questions": [],
            "summary": "The relationship and timeline conflict.",
        }
    )

    proposal = await ModelAnalysisService(override_db_session).analyze_ambiguity(
        case.id,
        provider,
        provider_name="fixture",
        model="fixture-v1",
        evidence_ids=[evidence.id],
        claim_ids=[claim.id],
    )

    assert proposal.execution_outcome == "invalid"
    assert proposal.proposed_output is None


@pytest.mark.asyncio
async def test_ambiguity_analysis_can_abstain_and_preserve_refusal(override_db_session):
    case, evidence, claim = case_with_claim(override_db_session)
    abstention = FixtureProvider(
        {
            "subject_name": "Jordan Example",
            "identity_status": "ambiguous",
            "relationship": "unclear",
            "relationship_time": "unclear",
            "operating_status": "unknown",
            "support_dimensions": [],
            "evidence_ids": [evidence.id],
            "claim_ids": [claim.id],
            "contradictions": [],
            "unresolved_questions": ["Is there an independent geographic match?"],
            "summary": "The supplied evidence is insufficient to resolve identity.",
        }
    )
    service = ModelAnalysisService(override_db_session)

    proposal = await service.analyze_ambiguity(
        case.id,
        abstention,
        provider_name="fixture",
        model="fixture-v1",
        evidence_ids=[evidence.id],
        claim_ids=[claim.id],
    )
    refusal = await service.extract_business(
        case.id,
        FixtureProvider(error=AIProviderRefusalError("provider detail must not persist")),
        provider_name="fixture",
        model="fixture-v1",
        evidence_ids=[evidence.id],
        claim_ids=[claim.id],
    )

    assert proposal.execution_outcome == "completed"
    assert proposal.proposed_output["identity_status"] == "ambiguous"
    assert refusal.execution_outcome == "refusal"
    assert refusal.proposed_output is None
    assert refusal.error_class == "AIProviderRefusalError"
