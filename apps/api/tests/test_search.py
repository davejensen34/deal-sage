import pytest
from sqlalchemy import func, select

from app.domain.models import CaseEvidence, ResearchQuery, Source, SourceCandidate, SourceCandidateDiscovery
from app.research.cases import ResearchCaseService
from app.research.search import FixtureSearchProvider, SearchResult, SearchService


def result(url: str = "https://Publisher.Example/obituary/one#details") -> SearchResult:
    return SearchResult(
        url=url,
        title="Public result title",
        publisher="Example Publisher",
        likely_source_type="obituary",
        geography={"state": "CO"},
        relevance_reason="The result may contain a business relationship clue.",
        proposed_use="case_specific_research",
        access_observations={"authentication_required": False},
    )


@pytest.mark.asyncio
async def test_search_stages_candidates_without_creating_evidence(override_db_session):
    case = ResearchCaseService(override_db_session).create_case(
        "signal_first", {"max_queries": 2}
    )
    service = SearchService(override_db_session)

    candidates = await service.execute(
        case.id,
        FixtureSearchProvider([result()]),
        '"Example Person" obituary business',
        max_results=5,
    )

    assert len(candidates) == 1
    assert candidates[0].canonical_url == "https://publisher.example/obituary/one"
    assert candidates[0].status == "candidate"
    assert override_db_session.scalar(
        select(func.count(CaseEvidence.id)).where(CaseEvidence.case_id == case.id)
    ) == 0
    query = override_db_session.scalar(select(ResearchQuery).where(ResearchQuery.case_id == case.id))
    assert query.status == "succeeded"
    assert query.result_count == 1


@pytest.mark.asyncio
async def test_search_budget_and_provider_limit_are_enforced(override_db_session):
    case = ResearchCaseService(override_db_session).create_case(
        "business_first", {"max_queries": 1}
    )
    service = SearchService(override_db_session)
    provider = FixtureSearchProvider([result()])
    await service.execute(case.id, provider, "first bounded query")

    with pytest.raises(ValueError, match="budget is exhausted"):
        await service.execute(case.id, provider, "second query")
    with pytest.raises(ValueError, match="between 1 and 20"):
        await service.execute(case.id, provider, "oversized query", max_results=21)


@pytest.mark.asyncio
async def test_provider_failure_records_only_safe_error_class(override_db_session):
    case = ResearchCaseService(override_db_session).create_case(
        "hybrid", {"max_queries": 1}
    )
    service = SearchService(override_db_session)

    with pytest.raises(RuntimeError, match="secret response body"):
        await service.execute(
            case.id,
            FixtureSearchProvider(error=RuntimeError("secret response body")),
            "bounded failure query",
        )

    query = override_db_session.scalar(select(ResearchQuery).where(ResearchQuery.case_id == case.id))
    assert query.status == "failed"
    assert query.error_class == "RuntimeError"
    assert "secret response body" not in query.error_class


@pytest.mark.asyncio
async def test_duplicate_results_do_not_inflate_source_candidates(override_db_session):
    case = ResearchCaseService(override_db_session).create_case(
        "signal_first", {"max_queries": 1}
    )
    duplicate_url = "https://example.test/public/item"
    await SearchService(override_db_session).execute(
        case.id,
        FixtureSearchProvider([result(duplicate_url), result(f"{duplicate_url}#copy")]),
        "deduplicated query",
    )

    assert override_db_session.scalar(
        select(func.count(SourceCandidate.id)).where(SourceCandidate.case_id == case.id)
    ) == 1
    query_id = override_db_session.scalar(
        select(ResearchQuery.id).where(ResearchQuery.case_id == case.id)
    )
    assert override_db_session.scalar(
        select(func.count(SourceCandidateDiscovery.id)).where(
            SourceCandidateDiscovery.query_id == query_id
        )
    ) == 1


@pytest.mark.asyncio
async def test_source_promotion_is_explicit(override_db_session):
    case = ResearchCaseService(override_db_session).create_case(
        "signal_first", {"max_queries": 1}
    )
    service = SearchService(override_db_session)
    candidate = (
        await service.execute(
            case.id,
            FixtureSearchProvider([result()]),
            "promotion candidate query",
        )
    )[0]
    known_source = Source(
        source_type="obituary",
        publisher="Evaluated Publisher",
        canonical_url="https://publisher.example",
        source_metadata={"evaluation": "manual"},
        reliability="medium",
        is_demo=False,
    )
    override_db_session.add(known_source)
    override_db_session.commit()
    override_db_session.refresh(known_source)

    promoted = service.promote(
        candidate.id,
        known_source.id,
        decision_reason="Repeated usefulness and access contract were manually reviewed.",
    )

    assert promoted.status == "promoted"
    assert promoted.promoted_source_id == known_source.id


def test_search_metrics_are_aggregate_only(client):
    response = client.get("/api/research/case-metrics")

    assert response.status_code == 200
    assert "search_queries" in response.json()
    assert "source_candidates" in response.json()
    assert "query_text" not in str(response.json())
