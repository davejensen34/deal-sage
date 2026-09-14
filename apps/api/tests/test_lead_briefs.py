from datetime import datetime

from app.domain.models import ClaimContradiction, ConfidenceAssessment, ModelProposal, AnalystConclusion
from app.research.cases import ResearchCaseService
from app.api.routes import research_case_narratives
from sqlalchemy import func, select


def fictional_cases(db):
    cases = ResearchCaseService(db)
    ids = []
    for i, (name, date, status, extra) in enumerate([
        ("Summit Tool Works", "2026-09-01", "reported", {"employee_count": "24, reported by company", "business_activity": "Repairs industrial pumps", "city": "Ogden", "state": "UT"}),
        ("Canyon Components", "2023-02-01", "completed", {"city": "Denver", "state": "CO"}),
        ("Prairie Systems", "2026-09-02", "reported", {"company_type": "public", "state": "TX"}),
        ("Mesa Services", "2026-10-01", "planned", {"industry": "Commercial maintenance", "state": "CO"}),
        ("Ridge Fabrication", "2026-09-03", "reported", {"state": "UT"}),
    ]):
        case = cases.create_case("hybrid", signal_intake_policy={"version": "signal-intake-v1", "assessment_date": "2026-09-14", "lookback_days": 90})
        text = f"Fictional fixture: {name} reports Jordan's retirement {date}. The announcement was made 2026-09-01."
        evidence = cases.add_evidence(case.id, source_mode="case_specific_research", canonical_url=f"https://example.test/brief/{i}",
            publisher="Fictional business journal", source_type="newspaper", content=text.encode(), relevant_excerpt=text,
            extracted_facts={"business_name": name, **extra}, provenance={"fixture": True}, published_at=datetime(2026, 9, 1))
        claim = cases.add_claim(case.id, evidence.id, subject_type="person", predicate="transition",
            object_value={"business": name, "person": "Jordan", "signal_type": "retirement", "event_date": date,
                "event_status": status, "event_date_excerpt": text, "announcement_date": "2026-09-01", "announcement_date_excerpt": text},
            confidence=.7, classification="source_fact", source_authority="publisher", directness="direct_statement")
        if i == 4:
            other = cases.add_claim(case.id, evidence.id, subject_type="person", predicate="transition",
                object_value={"business": name, "person": "Jordan", "signal_type": "retirement", "event_date": "2026-08-01", "event_status": "cancelled"},
                confidence=.7, classification="source_fact", source_authority="publisher", directness="direct_statement")
            db.add(ClaimContradiction(case_id=case.id, left_claim_id=claim.id, right_claim_id=other.id,
                contradiction_type="timeline", rationale="A second retained claim says the retirement was cancelled.", status="open"))
            db.commit()
        ids.append(case.id)
    return [row for row in research_case_narratives(db)["cases"] if row["id"] in ids]


def test_briefs_preserve_business_value_unknowns_and_freshness(override_db_session):
    db = override_db_session
    counts = [db.scalar(select(func.count(model.id))) for model in (ConfidenceAssessment, ModelProposal, AnalystConclusion)]
    rows = {r["lead_brief"]["title"]: r for r in fictional_cases(db)}
    recent = rows["Summit Tool Works"]["lead_brief"]
    assert recent["category"] == "recent" and recent["order"] == 0
    assert any(f["label"] == "Employees" and f["evidence_id"] for f in recent["facts"])
    assert not any(f["label"] in {"Revenue", "EBITDA"} for f in recent["facts"])
    assert "who runs" in recent["why_it_matters"]
    assert rows["Canyon Components"]["lead_brief"]["category"] == "background"
    assert "historical" in rows["Canyon Components"]["lead_brief"]["why_it_matters"]
    assert rows["Prairie Systems"]["lead_brief"]["target_fit"] == "public_company_reported"
    assert rows["Prairie Systems"]["lead_brief"]["order"] == 2
    assert rows["Mesa Services"]["lead_brief"]["timing"]["route"] == "planned_event"
    assert rows["Ridge Fabrication"]["lead_brief"]["conflicts"]
    assert rows["Ridge Fabrication"]["lead_brief"]["category"] == "date_review"
    assert counts == [db.scalar(select(func.count(model.id))) for model in (ConfidenceAssessment, ModelProposal, AnalystConclusion)]


def test_signal_first_unknown_business_is_not_replaced_with_hypothesis(client, override_db_session):
    case = ResearchCaseService(override_db_session).create_case("signal_first")
    row = next(r for r in client.get("/api/research/case-narratives").json()["cases"] if r["id"] == case.id)
    assert row["lead_brief"]["title"] == "Business not yet identified"
    assert row["lead_brief"]["facts"] == []
    assert row["lead_brief"]["category"] == "date_review"


def test_ambiguous_names_and_estimates_are_not_resolved_into_a_company(override_db_session):
    db = override_db_session
    service = ResearchCaseService(db)
    case = service.create_case("business_first")
    evidence = service.add_evidence(case.id, source_mode="case_specific_research",
        canonical_url="https://example.test/estimate", publisher="Fictional directory",
        source_type="directory", content=b"Fictional ambiguous company estimate",
        relevant_excerpt="Fictional ambiguous company estimate",
        extracted_facts={"business_name": "First Name", "company_type": "public", "revenue": "USD 2m estimate"},
        provenance={"fixture": True}, classification="third_party_estimate")
    service.add_claim(case.id, evidence.id, subject_type="business", predicate="identity",
        object_value={"business": "Second Name"}, confidence=.2,
        classification="third_party_estimate", source_authority="directory", directness="indirect")
    brief = next(r["lead_brief"] for r in research_case_narratives(db)["cases"] if r["id"] == case.id)
    assert brief["title"] == "Multiple business names reported"
    assert brief["target_fit"] == "conflicting"
    assert brief["reported_names"] == ["First Name", "Second Name"]
    assert all(f["classification"] == "third_party_estimate" for f in brief["facts"])
    assert "public company, outside" not in brief["why_it_matters"]
    assert "conflicting" in brief["next_gap"]
