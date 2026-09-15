from datetime import datetime

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.domain.models import AnalystConclusion, CandidateMatch, ResearchCase
from app.main import app
from app.research.cases import ResearchCaseService


@pytest.fixture
def inbox_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        previous = app.dependency_overrides[get_db]
        app.dependency_overrides[get_db] = lambda: db
        try:
            yield db
        finally:
            app.dependency_overrides[get_db] = previous
    engine.dispose()


def add_signal(db, *, state="UT", event_date=None, published=None, signal="retirement"):
    service = ResearchCaseService(db)
    case = service.create_case("signal_first")
    evidence = service.add_evidence(case.id, source_mode="case_specific_research",
        canonical_url=f"https://example.test/inbox/{case.id}", publisher="Fictional source",
        source_type="company_website", content=f"Fictional case {case.id}".encode(),
        relevant_excerpt="Fictional business transition", extracted_facts={"state": state}, provenance={"fixture": True})
    evidence.published_at = datetime.fromisoformat(published) if published else None
    claim = service.add_claim(case.id, evidence.id, subject_type="person", predicate="transition",
        object_value={"signal_type": signal, "event_status": "reported", "event_date": event_date},
        confidence=.5, classification="source_fact", source_authority="company", directness="direct_statement")
    db.commit()
    return case, claim


def test_pagination_keeps_unresolved_cases_and_stable_ties(client, inbox_db):
    for _ in range(23):
        case = ResearchCaseService(inbox_db).create_case("signal_first")
        case.updated_at = datetime(2026, 9, 15)
    inbox_db.commit()
    pages = [client.get(f"/api/research/inbox?page={page}").json() for page in [1, 2, 3]]
    assert [len(p["cases"]) for p in pages] == [10, 10, 3]
    assert all(p["total"] == 23 for p in pages)
    rows = [r for p in pages for r in p["cases"]]
    assert [r["id"] for r in rows] == list(range(23, 0, -1))
    assert all(r["lead_brief"]["title"] == "Business not yet identified" for r in rows)
    assert all(r["linked_business"] is None and r["candidate_match_id"] is None for r in rows)
    assert inbox_db.scalar(select(func.count(CandidateMatch.id))) == 0
    assert client.get("/api/research/cases/1").json()["id"] == 1
    assert client.get("/api/research/cases/999").status_code == 404
    assert client.get("/api/research/inbox?page=0").status_code == 422
    assert client.get("/api/research/inbox?page_size=51").status_code == 422


def test_dates_do_not_substitute_publication_or_retrieval_for_event(client, inbox_db):
    recent, _ = add_signal(inbox_db, event_date="2026-09-01", published="2026-09-02")
    old, _ = add_signal(inbox_db, event_date="2000-01-01", published="2026-09-03")
    unknown, _ = add_signal(inbox_db, published="2026-09-04")
    other, _ = add_signal(inbox_db, state="CO", event_date="2026-09-05")
    malformed, claim = add_signal(inbox_db)
    claim.object_value = {**claim.object_value, "event_date": "2026-09-00"}
    inbox_db.commit()
    base = "/api/research/inbox?state=UT&signal=retirement&since=2026-09-01&until=2026-09-15"
    assert {r["id"] for r in client.get(base).json()["cases"]} == {recent.id}
    assert {r["id"] for r in client.get(base+"&date_basis=announcement").json()["cases"]} == {recent.id, old.id, unknown.id}
    assert client.get("/api/research/inbox?state=UT").json()["total"] == 4
    assert client.get(base.replace("retirement", "succession")).json()["total"] == 0
    assert client.get("/api/research/inbox?since=2026-09-15&until=2026-09-01").status_code == 422
    assert client.get("/api/research/inbox?date_basis=retrieved").status_code == 422


def test_human_conclusion_is_separate_and_dashboard_accepts_empty_store(client, inbox_db):
    case = ResearchCaseService(inbox_db).create_case("hybrid")
    inbox_db.add(AnalystConclusion(case_id=case.id, analyst_name="Fictional reviewer",
        outcome="needs_more_research", statement="Identity is unresolved.", status="draft"))
    inbox_db.commit()
    row = client.get("/api/research/cases/1").json()
    assert row["status"] == "open"
    assert row["conclusion"]["analyst"] == "Fictional reviewer"
    assert row["conclusion"]["status"] == "draft"
    assert row["confidence"] is None
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    assert response.json()["metrics"]["average_confidence"] is None
    assert response.json()["recent_candidates"] == []


def test_dashboard_only_lists_candidates_awaiting_review(client):
    response = client.get("/api/dashboard").json()
    assert all(r["status"] in {"new", "researching", "needs_review"} for r in response["recent_candidates"])
