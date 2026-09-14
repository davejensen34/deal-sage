from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select, text, create_engine
from sqlalchemy.orm import Session
from alembic import command

from app.domain.models import AuditEvent, CaseEvidence, ClaimContradiction, EvidenceClaim, ModelProposal, ResearchCase, ResearchStep, SourceCandidate
from app.ops.schema import alembic_config
from app.research.cases import ResearchCaseService
from app.research.frontier import ResearchPlanner
from app.research.model_analysis import ModelAnalysisService
from app.research.search import FixtureSearchProvider, SearchService
from app.research.signal_freshness import assess_signal, case_signal_intake, require_recent_signal, validate_policy
from app.research.leads import discovery_leads

POLICY = {"version": "signal-intake-v1", "assessment_date": "2026-09-14", "lookback_days": 90}


def pair(event=None, announcement=None, status="reported", *, supported=True):
    value = {"person": "Jordan Example", "signal_type": "retirement", "event_status": status,
             "event_date": event, "announcement_date": announcement}
    excerpt = f"Fictional statement: event {event}; announcement {announcement}."
    if supported:
        value.update(event_date_excerpt=excerpt, announcement_date_excerpt=excerpt)
    claim = EvidenceClaim(id=1, case_id=1, evidence_id=1, subject_type="person", predicate="transition",
                          object_value=value, status="asserted", confidence=0.8,
                          classification="source_fact", source_authority="publisher", directness="direct_statement")
    evidence = CaseEvidence(id=1, case_id=1, source_mode="case_specific_research",
                            canonical_url="https://example.test/signal", publisher="Fictional publisher",
                            source_type="newspaper", content_hash="a" * 64, classification="source_fact",
                            relevant_excerpt=excerpt, published_at=datetime(2026, 9, 14, tzinfo=timezone.utc),
                            retrieved_at=datetime(2026, 9, 14, tzinfo=timezone.utc))
    return claim, evidence


@pytest.mark.parametrize("event,announcement,status,route", [
    ("2026-06-16", None, "completed", "recent_event"),  # inclusive 90-day boundary
    ("2026-06-15", "2026-09-14", "completed", "background"),
    ("2024-01-01", "2026-09-14", "reported", "background"),
    ("2026-09-14", None, "reported", "recent_event"),
    (None, "2026-09-01", "unknown", "recent_announcement"),
    (None, None, "unknown", "date_verification"),
    (None, "2024-01-01", "unknown", "background"),
    ("2026-10-01", "2026-09-01", "planned", "planned_event"),
    ("2026-10-01", None, "planned", "date_verification"),
    ("2026-10-01", "2026-09-01", "completed", "date_verification"),
    ("2026-09-01", "2026-09-01", "planned", "date_verification"),
    ("2026-09-01", "2026-09-01", "cancelled", "background"),
    (None, "2026-10-01", "unknown", "date_verification"),
    ("invalid", None, "reported", "date_verification"),
])
def test_date_routes(event, announcement, status, route):
    claim, evidence = pair(event, announcement, status)
    result = assess_signal(claim, evidence, POLICY)
    assert result["route"] == route
    assert result["event_status"] == status
    assert result["publication_date"] != result["event_date"]
    assert result["claim_id"] == claim.id and result["evidence_id"] == evidence.id


def test_recent_event_in_old_updated_source_and_untrusted_metadata():
    claim, evidence = pair("2026-09-01")
    evidence.published_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert assess_signal(claim, evidence, POLICY)["eligible"]
    claim, evidence = pair(None)
    evidence.extracted_facts = {"copyright_year": 2026, "search_provider_date": "2026-09-14"}
    assert not assess_signal(claim, evidence, POLICY)["eligible"]
    claim, evidence = pair("2026-09-01", supported=False)
    assert assess_signal(claim, evidence, POLICY)["reason"] == "event_date_needs_source_support"
    claim.object_value["event_date_excerpt"] = "Not in the retained source"
    assert not assess_signal(claim, evidence, POLICY)["eligible"]


@pytest.mark.parametrize("update", [{"lookback_days": 0}, {"lookback_days": True}, {"lookback_days": 3651},
                                  {"lookback_days": "90"}, {"version": "unknown"},
                                  {"assessment_date": "2026-02-30"}, {"assessment_date": "0001-01-01"},
                                  {"extra": 1}])
def test_invalid_policy(update):
    with pytest.raises(ValueError):
        validate_policy(POLICY | update)


def stored_pair(db, event="2024-01-01"):
    case = ResearchCaseService(db).create_case("signal_first", {"max_queries": 3, "max_model_calls": 3},
                                               signal_intake_policy=POLICY)
    claim, evidence = pair(event)
    claim.id = evidence.id = None
    claim.case_id = evidence.case_id = case.id
    db.add(evidence)
    db.flush()
    claim.evidence_id = evidence.id
    db.add(claim)
    db.commit()
    return case, claim, evidence


@pytest.mark.asyncio
async def test_stale_intake_cannot_reserve_or_call_model(client, override_db_session):
    db = override_db_session
    case, claim, evidence = stored_pair(db)
    planner = ResearchPlanner(db)
    item = planner.add_item(case.id, question_type="verify_transition_identity", question="Verify date", rationale="Fixture", priority=50)
    with pytest.raises(ValueError, match="No eligible recent signal"):
        planner.start_step(case.id, item.id, action_type="model_analysis", provider="fixture", model="fixture", prompt_version="v1")
    assert item.status == "pending" and item.attempts == 0
    assert db.scalar(select(func.count(ResearchStep.id)).where(ResearchStep.case_id == case.id)) == 0

    class NeverCall:
        async def extract_structured(self, *args):
            pytest.fail("Stale evidence reached a provider")

    with pytest.raises(ValueError, match="No eligible recent signal"):
        await ModelAnalysisService(db).extract_business(case.id, NeverCall(), provider_name="fixture", model="fixture",
                                                       evidence_ids=[evidence.id], claim_ids=[claim.id])
    assert db.scalar(select(func.count(ModelProposal.id)).where(ModelProposal.case_id == case.id)) == 0
    assert db.get(CaseEvidence, evidence.id) is not None
    row = next(row for row in client.get("/api/research/case-narratives").json()["cases"] if row["id"] == case.id)
    assert row["signal_intake"]["route_counts"] == {"background": 1}
    assert row["signal_intake"]["eligible_signal_count"] == 0


@pytest.mark.asyncio
async def test_eligible_packet_has_frozen_policy_and_audit(override_db_session):
    db = override_db_session
    case, claim, evidence = stored_pair(db, "2026-09-01")

    class Capture:
        async def extract_structured(self, prompt, schema):
            assert '"assessment_date": "2026-09-14"' in prompt
            assert '"eligible_signal_count": 1' in prompt
            return {"observations": [{"field": "legal_name", "value": "Fictional Company",
                                      "evidence_ids": [evidence.id], "claim_ids": []}],
                    "unresolved_questions": [], "summary": "Fictional business observation"}

    result = await ModelAnalysisService(db).extract_business(case.id, Capture(), provider_name="fixture", model="fixture",
                                                           evidence_ids=[evidence.id], claim_ids=[claim.id])
    assert result.execution_outcome == "completed"
    audit = db.scalar(select(AuditEvent).where(AuditEvent.action == "signal_intake_analysis"))
    assert audit.after_state["intake"]["policy"] == POLICY
    assert "relevant_excerpt" not in str(audit.after_state)


def test_conflict_outside_selected_packet_prevents_cherry_picking(override_db_session):
    db = override_db_session
    case, first, evidence = stored_pair(db, "2026-09-01")
    second, other = pair("2024-01-01")
    second.id = other.id = None
    second.case_id = other.case_id = case.id
    db.add(other)
    db.flush()
    second.evidence_id = other.id
    db.add(second)
    db.commit()
    report = case_signal_intake(db, case.id, evidence_ids=[evidence.id])
    assert report["signals"][0]["reason"] == "conflicting_event_dates"
    assert not report["analysis_allowed"]


def test_selected_claim_scope_and_open_conflict(override_db_session):
    db = override_db_session
    case, claim, evidence = stored_pair(db, "2026-09-01")
    with pytest.raises(ValueError, match="No eligible"):
        require_recent_signal(db, case.id, evidence_ids=[evidence.id], claim_ids=[])
    db.add(ClaimContradiction(case_id=case.id, left_claim_id=claim.id, right_claim_id=claim.id,
                              contradiction_type="timeline", rationale="Fixture conflict", status="open"))
    db.commit()
    assert case_signal_intake(db, case.id)["signals"][0]["reason"] == "open_claim_conflict"


def test_freshness_priority_preserves_untrusted_and_blocked_leads(override_db_session):
    db = override_db_session
    case, claim, evidence = stored_pair(db, "2026-09-01")
    candidate = SourceCandidate(case_id=case.id, canonical_url=evidence.canonical_url, domain="example.test",
                                likely_source_type="newspaper", geography={}, relevance_reason="Fixture",
                                proposed_use="case_specific_research", search_provider="fixture",
                                access_observations={}, access_decision="blocked")
    db.add(candidate)
    db.commit()
    lead = discovery_leads(db, case.id)[0]
    assert lead["priority"] == 65 and lead["method"] == "discovery-priority-v2"
    assert lead["next_action"] == "find_alternative"
    assert lead["signal_freshness"][0]["eligible"]
    # Retain all evidence; changing the assessment policy changes routing only.
    case.signal_intake_policy = POLICY | {"assessment_date": "2027-09-14"}
    db.commit()
    old = discovery_leads(db, case.id)[0]
    assert old["priority"] == 30 and old["signal_freshness"][0]["route"] == "background"
    assert old["evidence_ids"] == [evidence.id]


@pytest.mark.asyncio
async def test_dated_discovery_and_empty_cohort_do_not_fill_slots(override_db_session):
    db = override_db_session
    case = ResearchCaseService(db).create_case("hybrid", {"max_queries": 3}, signal_intake_policy=POLICY)

    class Capture(FixtureSearchProvider):
        async def search(self, query, max_results):
            assert query == "retirement after:2026-06-15 before:2026-09-15"
            return []

    assert await SearchService(db).execute(case.id, Capture([]), "retirement") == []
    assert not case_signal_intake(db, case.id)["analysis_allowed"]
    for query in (" ", "x" * 490):
        with pytest.raises(ValueError, match="500 characters"):
            await SearchService(db).execute(case.id, Capture([]), query)
    old = ResearchCaseService(db).create_case("business_first")
    assert case_signal_intake(db, old.id) is None


def test_migration_preserves_existing_cases_and_refuses_policy_loss(tmp_path):
    url = f"sqlite:///{tmp_path / 'freshness.db'}"
    cfg = alembic_config(url)
    command.upgrade(cfg, "a729e10b3c42")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO research_cases (origin_strategy,status,research_budget,confidence,created_at,updated_at) "
                                "VALUES ('hybrid','open','{}','{}',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"))
    command.upgrade(cfg, "head")
    with Session(engine) as db:
        old = db.get(ResearchCase, 1)
        assert old.origin_strategy == "hybrid" and old.signal_intake_policy is None
    command.downgrade(cfg, "a729e10b3c42")
    command.upgrade(cfg, "head")
    with Session(engine) as db:
        ResearchCaseService(db).create_case("hybrid", signal_intake_policy=POLICY)
    with pytest.raises(RuntimeError, match="Cannot remove configured"):
        command.downgrade(cfg, "a729e10b3c42")
