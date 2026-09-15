"""Case-local access judgments and bounded reads; never external execution."""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.service import Identity, current_identity, require_permission
from app.core.database import get_db
from app.domain.models import CaseEvidence, EvidenceClaim, ResearchCase, SourceCandidate
from app.research.discovery_runs import utc
from app.research.retrieval import BLOCKING_ACCESS_FLAGS
from app.research.search import SearchService

router = APIRouter(prefix="/api/research/cases", dependencies=[Depends(current_identity)])


def require_case(db, case_id):
    if db.get(ResearchCase, case_id) is None:
        raise HTTPException(404, "Research case not found")


def source_view(row):
    return {"id": row.id, "url": row.canonical_url, "publisher": row.publisher or row.domain,
        "source_type": row.likely_source_type, "access": row.access_decision,
        "reason": row.access_decision_reason, "reviewer": row.access_decided_by,
        "reviewed_at": utc(row.access_decided_at) if row.access_decided_at else None,
        "blocking_observations": sorted(flag for flag in BLOCKING_ACCESS_FLAGS if row.access_observations.get(flag) is True)}


@router.get("/{case_id}/investigation/sources")
def sources(case_id: int, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    require_case(db, case_id)
    rows = db.scalars(select(SourceCandidate).where(SourceCandidate.case_id == case_id)
        .order_by(SourceCandidate.id).offset((page-1)*20).limit(21)).all()
    return {"items": [source_view(row) for row in rows[:20]], "has_next": len(rows)>20}


class AccessDecision(BaseModel):
    decision: Literal["approved", "blocked"]
    reason: str = Field(min_length=5, max_length=1000)
    reviewed_conditions: bool = False


@router.post("/{case_id}/investigation/sources/{source_id}/access")
def decide(case_id: int, source_id: int, payload: AccessDecision, db: Session = Depends(get_db),
           identity: Identity = Depends(require_permission("review"))):
    source = db.get(SourceCandidate, source_id)
    if source is None or source.case_id != case_id:
        raise HTTPException(404, "Source not found in this case")
    if len(payload.reason.strip()) < 5:
        raise HTTPException(422, "Explain the access decision in at least five characters")
    if payload.decision == "approved":
        if not payload.reviewed_conditions:
            raise HTTPException(422, "Review the source access conditions before approving retrieval")
        if source_view(source)["blocking_observations"]:
            raise HTTPException(409, "Recorded access restrictions prevent approval; the clue remains available")
    try:
        return source_view(SearchService(db).decide_access(source_id, decision=payload.decision,
            reason=payload.reason, decided_by=identity.display_name, user_id=identity.user_id))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/{case_id}/investigation/evidence")
def evidence(case_id: int, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    require_case(db, case_id)
    rows = db.scalars(select(CaseEvidence).where(CaseEvidence.case_id == case_id)
        .order_by(CaseEvidence.id).offset((page-1)*20).limit(21)).all()
    # Expose evidence lineage, not private storage keys, request metadata or raw bytes.
    return {"items": [{"id": row.id, "url": row.canonical_url, "publisher": row.publisher,
        "classification": row.classification, "source_type": row.source_type,
        "published_at": utc(row.published_at) if row.published_at else None,
        "retrieved_at": utc(row.retrieved_at), "content_hash": row.content_hash,
        "artifact_id": row.raw_artifact_id, "excerpt": (row.relevant_excerpt or "")[:2000],
        "excerpt_truncated": len(row.relevant_excerpt or "")>2000} for row in rows[:20]], "has_next": len(rows)>20}


@router.get("/{case_id}/investigation/evidence/{evidence_id}/claims")
def claims(case_id: int, evidence_id: int, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    item = db.get(CaseEvidence, evidence_id)
    if item is None or item.case_id != case_id:
        raise HTTPException(404, "Evidence not found in this case")
    rows = db.scalars(select(EvidenceClaim).where(EvidenceClaim.case_id == case_id,
        EvidenceClaim.evidence_id == evidence_id).order_by(EvidenceClaim.id).offset((page-1)*20).limit(21)).all()
    return {"items": [{"id": row.id, "subject": row.subject_type, "predicate": row.predicate,
        "value": row.object_value, "relationship": row.relationship_semantics,
        "classification": row.classification, "status": row.status,
        "authority": row.source_authority, "directness": row.directness} for row in rows[:20]], "has_next": len(rows)>20}
