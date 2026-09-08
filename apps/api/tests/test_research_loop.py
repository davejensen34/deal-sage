from datetime import datetime, timezone

import pytest

from app.domain.models import ResearchStep
from app.research.cases import ResearchCaseService
from app.research.frontier import ResearchPlanner
from app.research.loop import ResearchLoopService
from app.research.model_proposals import ModelProposalService
from app.research.plan_approval import ResearchPlanApprovalService
from app.research.retrieval import FixtureDocumentProvider, RetrievedDocument
from app.research.search import FixtureSearchProvider, SearchResult, SearchService
from app.storage.local import LocalEvidenceStorage


def case_with_plan(db):
    cases = ResearchCaseService(db)
    case = cases.create_case(
        "signal_first",
        {
            "max_queries": 3,
            "max_documents": 3,
            "max_steps": 10,
            "max_elapsed_seconds": 900,
        },
    )
    evidence = cases.add_evidence(
        case.id,
        source_mode="case_specific_research",
        canonical_url="https://seed.example.test/signal",
        publisher="Fictional Signal Publisher",
        source_type="obituary",
        content=b"A fictional transition signal with a possible trade clue.",
        relevant_excerpt="A fictional transition signal with a possible trade clue.",
        extracted_facts={"occupation_clue": "tool repair"},
        provenance={"provider": "fixture"},
    )
    proposal = ModelProposalService(db).record(
        case.id,
        task="research_plan",
        provider="fixture",
        model="fixture-v1",
        prompt_version="research-plan-v1",
        schema_version="research-plan-v1",
        execution_outcome="completed",
        proposed_output={
            "question_type": "find_independent_evidence",
            "question": "Does the signal identify a related operating business?",
            "rationale": "The trade clue warrants one bounded independent search.",
            "next_action": "search",
            "query": "Colorado tool repair transition notice",
            "source_type": "government",
            "evidence_ids": [evidence.id],
            "claim_ids": [],
            "expected_information_gain": "An independent source may identify a business.",
        },
        supported_evidence_ids=[evidence.id],
    )
    item = ResearchPlanApprovalService(db).approve(proposal.id, priority=80)
    assert item is not None
    return case, item


def search_provider():
    return FixtureSearchProvider(
        [
            SearchResult(
                url="https://public.example.test/notices/1",
                title="Fictional notice",
                relevance_reason="Could independently identify a business.",
                proposed_use="case_specific_research",
                publisher="Fictional Public Notices",
                likely_source_type="probate_public_notice",
                geography={"state": "CO"},
                access_observations={"authentication_required": False},
            )
        ]
    )


@pytest.mark.asyncio
async def test_approved_plan_executes_search_then_permissioned_retrieval(
    override_db_session, tmp_path
):
    case, search_item = case_with_plan(override_db_session)
    loop = ResearchLoopService(override_db_session)

    search_execution = await loop.execute_search(
        case.id, search_item.id, search_provider(), max_results=1
    )

    assert len(search_execution.new_candidate_ids) == 1
    assert search_execution.step.result_summary["new_candidate_count"] == 1
    assert search_item.status == "resolved"
    candidate_id = search_execution.new_candidate_ids[0]
    SearchService(override_db_session).decide_access(
        candidate_id,
        decision="approved",
        reason="Bounded public retrieval reviewed for this fictional case.",
        decided_by="analyst@example.test",
    )
    retrieval_item = ResearchPlanner(override_db_session).add_item(
        case.id,
        question_type="verify_transition_identity",
        question="What does the approved public notice actually state?",
        rationale="Retrieval must precede evidence use.",
        priority=70,
        max_attempts=2,
    )
    document = RetrievedDocument(
        url="https://public.example.test/notices/1",
        content=b"Fictional notice naming Example Tool Repair.",
        media_type="text/plain",
        retrieved_at=datetime.now(timezone.utc),
    )

    retrieval = await loop.execute_retrieval(
        case.id,
        retrieval_item.id,
        candidate_id,
        FixtureDocumentProvider(document),
        LocalEvidenceStorage(tmp_path),
    )

    assert retrieval.new_evidence is True
    assert retrieval.evidence_id is not None
    assert retrieval_item.status == "resolved"

    repeated_item = ResearchPlanner(override_db_session).add_item(
        case.id,
        question_type="find_independent_evidence",
        question="Check whether the approved page has changed.",
        rationale="Exercise content-addressed convergence.",
        priority=50,
    )
    repeated = await loop.execute_retrieval(
        case.id,
        repeated_item.id,
        candidate_id,
        FixtureDocumentProvider(document),
        LocalEvidenceStorage(tmp_path),
    )
    assert repeated.evidence_id == retrieval.evidence_id
    assert repeated.new_evidence is False
    assert repeated_item.status == "pending"


@pytest.mark.asyncio
async def test_repeated_results_converge_without_duplicate_candidates(override_db_session):
    case, first_item = case_with_plan(override_db_session)
    loop = ResearchLoopService(override_db_session)
    await loop.execute_search(case.id, first_item.id, search_provider(), max_results=1)
    repeated_item = ResearchPlanner(override_db_session).add_item(
        case.id,
        question_type="find_independent_evidence",
        question="Repeat the bounded discovery check once.",
        rationale="Validate convergence behavior.",
        priority=60,
        max_attempts=2,
    )

    first_repeat = await loop.execute_search(
        case.id,
        repeated_item.id,
        search_provider(),
        query="Colorado tool repair transition notice",
        max_results=1,
    )
    second_repeat = await loop.execute_search(
        case.id,
        repeated_item.id,
        search_provider(),
        query="Colorado tool repair transition notice",
        max_results=1,
    )

    assert first_repeat.new_candidate_ids == ()
    assert second_repeat.new_candidate_ids == ()
    assert repeated_item.status == "blocked"
    assert loop.next_item(case.id) is None
    assert case.status == "stopped"
    assert case.stop_reason == "frontier_attempts_exhausted"


@pytest.mark.asyncio
async def test_approved_model_query_cannot_be_changed_at_execution(override_db_session):
    case, item = case_with_plan(override_db_session)

    with pytest.raises(ValueError, match="differs from the approved proposal"):
        await ResearchLoopService(override_db_session).execute_search(
            case.id,
            item.id,
            search_provider(),
            query="A broader query the model did not propose",
            max_results=1,
        )

    assert override_db_session.query(ResearchStep).filter_by(case_id=case.id).count() == 0


@pytest.mark.asyncio
async def test_provider_failure_is_audited_without_error_body(override_db_session):
    case, item = case_with_plan(override_db_session)
    loop = ResearchLoopService(override_db_session)

    with pytest.raises(RuntimeError, match="secret response body"):
        await loop.execute_search(
            case.id,
            item.id,
            FixtureSearchProvider(error=RuntimeError("secret response body")),
            max_results=1,
        )

    step = override_db_session.query(ResearchStep).filter_by(case_id=case.id).one()
    assert step.status == "failed"
    assert step.error_class == "RuntimeError"
    assert "secret" not in str(step.result_summary)
