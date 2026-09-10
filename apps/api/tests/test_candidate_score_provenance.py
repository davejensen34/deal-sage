from sqlalchemy import select

from app.domain.models import CandidateMatch, CandidateScoreAssessment
from app.services.candidate_scoring import record_score_assessment


def test_seeded_scores_have_explicit_legacy_provenance(client):
    detail = client.get("/api/candidates/1").json()

    assert detail["score_provenance"]["method_version"] == "candidate-score-v1"
    assert detail["score_provenance"]["classification"] == "legacy_demo_import"
    assert detail["score_provenance"]["supporting_evidence_ids"] == [1, 2]
    assert detail["score_provenance"]["calculation"]["corroboration_bonus"] == 5


def test_assessment_recalculates_and_projects_displayed_scores(override_db_session):
    db = override_db_session
    candidate = db.get(CandidateMatch, 2)
    assessment = record_score_assessment(
        db,
        candidate,
        owner_score=84,
        signal_score=67,
        contradiction_penalty=8,
        factors=[{"axis": "signal_identity", "feature": "stale_source", "impact": -8}],
        evidence_ids=[4, 3, 4],
    )
    db.commit()

    assert assessment.overall_candidate_confidence == 59
    assert candidate.overall_candidate_confidence == 59
    stored = db.scalar(
        select(CandidateScoreAssessment)
        .where(CandidateScoreAssessment.candidate_id == candidate.id)
        .order_by(CandidateScoreAssessment.id.desc())
    )
    assert stored.provenance_classification == "evidence_derived"
    assert stored.supporting_evidence_ids == [3, 4]
