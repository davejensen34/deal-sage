"""Persist reproducible candidate scores without upgrading inference to source fact."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import CandidateMatch, CandidateScoreAssessment
from app.domain.scoring import combine_scores


METHOD_VERSION = "candidate-score-v1"


def record_score_assessment(
    db: Session,
    candidate: CandidateMatch,
    *,
    owner_score: int,
    signal_score: int,
    factors: list[dict],
    evidence_ids: list[int],
    provenance_classification: str = "evidence_derived",
    contradiction_penalty: int = 0,
) -> CandidateScoreAssessment:
    """Calculate, persist, and project one score snapshot onto the queue row.

    Factor impacts remain explicit inputs. The service owns the conjunctive formula
    so API-visible totals cannot drift from the retained calculation record.
    """
    overall = combine_scores(owner_score, signal_score, contradiction_penalty)
    assessment = CandidateScoreAssessment(
        candidate_id=candidate.id,
        method_version=METHOD_VERSION,
        provenance_classification=provenance_classification,
        owner_business_confidence=owner_score,
        signal_identity_confidence=signal_score,
        contradiction_penalty=contradiction_penalty,
        overall_candidate_confidence=overall,
        factors=factors,
        supporting_evidence_ids=sorted(set(evidence_ids)),
        calculation={
            "formula": "min(owner_business, signal_identity) + corroboration_bonus - contradiction_penalty",
            "corroboration_bonus": 5 if owner_score >= 80 and signal_score >= 80 else 0,
            "clamp": [0, 100],
        },
    )
    candidate.owner_business_confidence = owner_score
    candidate.signal_identity_confidence = signal_score
    candidate.overall_candidate_confidence = overall
    db.add(assessment)
    return assessment


def ensure_score_assessments(db: Session) -> None:
    """Make legacy displayed scores reproducible without relabeling fixtures as facts."""
    assessed = set(db.scalars(select(CandidateScoreAssessment.candidate_id)).all())
    for candidate in db.scalars(select(CandidateMatch)).all():
        if candidate.id in assessed:
            continue
        evidence_ids = [e.id for e in candidate.evidence]
        # Older demo rows retained curated totals but not their per-axis inputs. We
        # preserve that limitation explicitly instead of inventing evidence lineage.
        record_score_assessment(
            db,
            candidate,
            owner_score=candidate.owner_business_confidence,
            signal_score=candidate.signal_identity_confidence,
            factors=[
                {"axis": "owner_business", "feature": "legacy_curated_total", "impact": candidate.owner_business_confidence},
                {"axis": "signal_identity", "feature": "legacy_curated_total", "impact": candidate.signal_identity_confidence},
            ],
            evidence_ids=evidence_ids,
            provenance_classification="legacy_demo_import",
        )
    db.commit()
