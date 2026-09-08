import pytest

from app.domain.models import ModelProposal
from app.research.cases import ResearchCaseService
from app.research.model_proposals import ModelProposalService
from app.research.proposal_dispositions import ModelProposalDispositionService


def proposal_fixture(db, *, outcome="completed"):
    cases = ResearchCaseService(db)
    case = cases.create_case("hybrid")
    evidence = cases.add_evidence(
        case.id,
        source_mode="case_specific_research",
        canonical_url="https://example.test/proposal-evidence",
        publisher="Fictional Publisher",
        source_type="business_website",
        content=b"Fictional evidence for analyst disposition.",
        relevant_excerpt="Fictional evidence for analyst disposition.",
        extracted_facts={"business_name": "Example Tool Works"},
        provenance={"provider": "fixture"},
    )
    proposal = ModelProposalService(db).record(
        case.id,
        task="business_extraction",
        provider="fixture",
        model="fixture-v1",
        prompt_version="business-extraction-v1",
        schema_version="business-extraction-v1",
        execution_outcome=outcome,
        proposed_output={"summary": "Example Tool Works"} if outcome == "completed" else None,
        supported_evidence_ids=[evidence.id],
        error_class=None if outcome == "completed" else "FixtureError",
    )
    return case, evidence, proposal


def test_correction_is_a_new_human_record_and_does_not_mutate_proposal(override_db_session):
    case, evidence, proposal = proposal_fixture(override_db_session)
    original = dict(proposal.proposed_output)

    disposition = ModelProposalDispositionService(override_db_session).add(
        proposal.id,
        analyst_name="Demo Analyst",
        decision="correct",
        rationale="The cited evidence uses the legal name, not the abbreviated name.",
        corrected_output={"summary": "Example Tool Works LLC"},
        supporting_evidence_ids=[evidence.id],
    )

    override_db_session.refresh(proposal)
    assert disposition.case_id == case.id
    assert disposition.corrected_output["summary"].endswith("LLC")
    assert proposal.proposed_output == original


def test_noncompleted_proposal_cannot_be_accepted_or_corrected(override_db_session):
    _, _, proposal = proposal_fixture(override_db_session, outcome="failed")
    service = ModelProposalDispositionService(override_db_session)

    for decision in ("accept", "correct"):
        with pytest.raises(ValueError, match="completed proposal"):
            service.add(
                proposal.id,
                analyst_name="Demo Analyst",
                decision=decision,
                rationale="Provider execution did not complete.",
                corrected_output={"summary": "human correction"} if decision == "correct" else None,
            )

    deferred = service.add(
        proposal.id,
        analyst_name="Demo Analyst",
        decision="defer",
        rationale="Retry only under a separately approved protocol.",
    )
    assert deferred.decision == "defer"


def test_disposition_lineage_cannot_cross_cases(override_db_session):
    _, _, proposal = proposal_fixture(override_db_session)
    _, other_evidence, _ = proposal_fixture(override_db_session)

    with pytest.raises(ValueError, match="same research case"):
        ModelProposalDispositionService(override_db_session).add(
            proposal.id,
            analyst_name="Demo Analyst",
            decision="reject",
            rationale="The proposed output is not supported.",
            supporting_evidence_ids=[other_evidence.id],
        )


def test_api_records_identity_and_exposes_distinct_proposal_layers(
    client, override_db_session
):
    case, evidence, proposal = proposal_fixture(override_db_session)

    response = client.post(
        f"/api/research/model-proposals/{proposal.id}/dispositions",
        json={
            "decision": "accept",
            "rationale": "The bounded proposal is supported by the cited evidence.",
            "supporting_evidence_ids": [evidence.id],
        },
    )

    assert response.status_code == 200
    assert response.json()["analyst"] == "Morgan Lee"
    narrative = client.get("/api/research/case-narratives").json()["cases"]
    item = next(entry for entry in narrative if entry["id"] == case.id)
    exposed = item["model_proposals"][0]
    assert exposed["proposed_output"] == proposal.proposed_output
    assert exposed["dispositions"][0]["decision"] == "accept"
    assert exposed["dispositions"][0]["rationale"].startswith("The bounded proposal")
    assert "Fictional evidence for analyst disposition" not in str(exposed)
