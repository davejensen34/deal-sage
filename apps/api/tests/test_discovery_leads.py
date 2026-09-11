import pytest
from sqlalchemy import func, select
from app.domain.models import AuditEvent, CaseEvidence, ConfidenceAssessment, ResearchFrontierItem
from app.research.cases import ResearchCaseService
from app.research.frontier import ResearchPlanner
from app.research.leads import discovery_leads
from app.research.search import FixtureSearchProvider, SearchResult, SearchService


async def discover(db, case_id):
    return (await SearchService(db).execute(case_id, FixtureSearchProvider([SearchResult(
        url="https://example.test/business", title="Possible business", publisher="Directory",
        relevance_reason="A possible local business connection, not confirmed.",
        proposed_use="case_specific_research", likely_source_type="business_directory",
    )]), "possible business"))[0]


@pytest.mark.asyncio
async def test_unverified_repeat_discovery_is_useful_without_becoming_evidence(client, override_db_session):
    db = override_db_session
    case = ResearchCaseService(db).create_case("signal_first", {"max_queries": 3})
    candidate = await discover(db, case.id)
    first = discovery_leads(db, case.id)[0]
    await discover(db, case.id)
    second = discovery_leads(db, case.id)[0]
    assert first["priority"] > 0 and first["priority"] == second["priority"]
    assert len(second["query_ids"]) == 2
    assert second["evidence_ids"] == []
    assert db.scalar(select(func.count(CaseEvidence.id)).where(CaseEvidence.case_id == case.id)) == 0
    assert db.scalar(select(func.count(ConfidenceAssessment.id)).where(ConfidenceAssessment.case_id == case.id)) == 0
    narrative = next(r for r in client.get("/api/research/case-narratives").json()["cases"] if r["id"] == case.id)
    assert narrative["discovery_leads"][0]["id"] == candidate.id
    assert narrative["confidence"] is None


@pytest.mark.asyncio
async def test_blocked_source_queues_alternative_without_acceptance_or_retry_reset(client, override_db_session):
    db = override_db_session
    case = ResearchCaseService(db).create_case("hybrid", {"max_queries": 3})
    candidate = await discover(db, case.id)
    before = discovery_leads(db, case.id)[0]["priority"]
    SearchService(db).decide_access(candidate.id, decision="blocked", reason="Access unavailable", decided_by="Policy")
    lead = discovery_leads(db, case.id)[0]
    assert lead["priority"] == before
    assert lead["next_action"] == "find_alternative"
    path = f"/api/research/cases/{case.id}/discovery-leads/{candidate.id}/follow-up"
    response = client.post(path)
    assert response.status_code == 200
    item = db.get(ResearchFrontierItem, response.json()["frontier_id"])
    assert item.question_type == "find_independent_evidence"
    assert item.supporting_claim_ids == []
    item.attempts = 2
    item.status = "blocked"
    db.commit()
    assert client.post(path).json()["frontier_id"] == item.id
    db.refresh(item)
    assert item.attempts == 2 and item.status == "blocked"
    assert db.scalar(select(func.count(AuditEvent.id)).where(AuditEvent.action == "discovery_followup_queued")) == 1
    db.refresh(candidate)
    assert candidate.access_decision == "blocked"
    assert response.json()["external_calls"] == 0
    # The repository suite shares its fixture database; don't leak frontier work
    # into older tests that assert a global empty frontier before their action.
    db.delete(item)
    db.commit()


@pytest.mark.asyncio
async def test_followup_rejects_cross_case_and_stopped_cases(client, override_db_session):
    db = override_db_session
    first = ResearchCaseService(db).create_case("business_first", {"max_queries": 3})
    other = ResearchCaseService(db).create_case("signal_first", {"max_queries": 3})
    candidate = await discover(db, first.id)
    assert client.post(f"/api/research/cases/{other.id}/discovery-leads/{candidate.id}/follow-up").status_code == 422
    ResearchPlanner(db).stop_case(first.id, "analyst_stopped")
    assert client.post(f"/api/research/cases/{first.id}/discovery-leads/{candidate.id}/follow-up").status_code == 422
    assert db.scalar(select(func.count(ResearchFrontierItem.id)).where(ResearchFrontierItem.case_id.in_([first.id, other.id]))) == 0


@pytest.mark.asyncio
async def test_retained_evidence_changes_action_not_opportunity_confidence(override_db_session):
    db = override_db_session
    case = ResearchCaseService(db).create_case("hybrid", {"max_queries": 3})
    candidate = await discover(db, case.id)
    evidence = ResearchCaseService(db).add_evidence(
        case.id, source_mode="case_specific_research", canonical_url=candidate.canonical_url,
        publisher="Directory", source_type="other", content=b"Uncertain business clue",
        relevant_excerpt="Uncertain business clue", extracted_facts={}, provenance={"candidate_id": candidate.id})
    lead = discovery_leads(db, case.id)[0]
    assert lead["next_action"] == "compare_evidence"
    assert lead["evidence_ids"] == [evidence.id]
    assert db.scalar(select(func.count(ConfidenceAssessment.id)).where(ConfidenceAssessment.case_id == case.id)) == 0


def test_viewer_cannot_queue_followup(client):
    from app.auth.service import Identity, current_identity
    from app.main import app
    app.dependency_overrides[current_identity] = lambda: Identity(None, "google", "viewer", None, "Viewer", role="viewer")
    try:
        assert client.post("/api/research/cases/1/discovery-leads/1/follow-up").status_code == 403
    finally:
        app.dependency_overrides.pop(current_identity, None)
