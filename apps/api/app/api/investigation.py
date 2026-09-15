"""Case-local investigation reads, access judgments and authorized retrieval."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.service import Identity, current_identity, require_permission
from app.core.database import get_db
from app.core.config import Settings, get_settings
from app.domain.models import CaseEvidence, EvidenceClaim, ResearchCase, SourceCandidate, RetrievalAttempt
from app.research import retrieval_attempts
from app.research.discovery_runs import utc
from app.research.retrieval import BLOCKING_ACCESS_FLAGS
from app.research.search import SearchService
from app.research.identity_resolution import evidence_relationship, normalize_identity
from app.research import extraction_attempts
from app.research import brief_versions, brief_comparisons
from app.domain.models import CaseBriefVersion, CaseDecision, AuditEvent
from app.research import case_decisions, development_briefs

router = APIRouter(prefix="/api/research/cases", dependencies=[Depends(current_identity)])


class SaveBriefVersion(BaseModel):
    request_key: UUID
    expected_hash: str = Field(pattern="^[0-9a-f]{64}$")
    expected_version: int = Field(ge=0)


@router.get('/{case_id}/brief-comparison')
def compare_briefs(case_id: int, from_version: int = Query(ge=1), to_version: int = Query(ge=1),
                   db: Session = Depends(get_db)):
    try:
        return brief_comparisons.compare(db, case_id, from_version, to_version)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/{case_id}/brief-preview")
def brief_preview(case_id: int, db: Session = Depends(get_db)):
    try:
        return brief_versions.preview(db,case_id)
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc


@router.get("/{case_id}/brief-versions")
def brief_history(case_id: int, page: int = Query(1,ge=1), db: Session = Depends(get_db)):
    require_case(db,case_id)
    rows=db.scalars(select(CaseBriefVersion).where(CaseBriefVersion.case_id==case_id)
        .order_by(CaseBriefVersion.version.desc()).offset((page-1)*10).limit(11)).all()
    return {"items":[brief_versions.view(row,False) for row in rows[:10]],"has_next":len(rows)>10}


@router.get("/{case_id}/brief-versions/{version}")
def brief_version(case_id: int, version: int, db: Session = Depends(get_db)):
    row=db.scalar(select(CaseBriefVersion).where(CaseBriefVersion.case_id==case_id,CaseBriefVersion.version==version))
    if row is None: raise HTTPException(404,"Brief version not found in this case")
    return brief_versions.view(row)


@router.post("/{case_id}/brief-versions")
def save_brief_version(case_id: int, payload: SaveBriefVersion, db: Session = Depends(get_db),
                      identity: Identity = Depends(require_permission("review"))):
    try:
        return brief_versions.save(db,case_id,request_key=payload.request_key,expected_hash=payload.expected_hash,
            expected_version=payload.expected_version,actor=identity.display_name,
            actor_key=extraction_attempts.digest([identity.provider,identity.subject]),user_id=identity.user_id)
    except ValueError as exc:
        db.rollback();raise HTTPException(409,str(exc)) from exc


class ExecuteExtraction(BaseModel):
    request_key: UUID
    expected_hash: str = Field(pattern="^[0-9a-f]{64}$")


@router.get("/{case_id}/investigation/evidence/{evidence_id}/extraction-preview")
def extraction_preview(case_id: int, evidence_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return extraction_attempts.preview(db, case_id, evidence_id, settings)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/{case_id}/investigation/extractions")
def extractions(case_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return extraction_attempts.history(db, case_id, settings)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/{case_id}/investigation/evidence/{evidence_id}/extract")
async def extract(case_id: int, evidence_id: int, payload: ExecuteExtraction,
                  db: Session = Depends(get_db), settings: Settings = Depends(get_settings),
                  identity: Identity = Depends(require_permission("execute_ai"))):
    try:
        return await extraction_attempts.execute(db, case_id, evidence_id, settings,
            request_key=payload.request_key, expected_hash=payload.expected_hash,
            actor=identity.display_name, actor_key=extraction_attempts.digest([identity.provider,identity.subject]),
            user_id=identity.user_id)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc


@router.post("/{case_id}/investigation/extractions/{attempt_id}/recover")
def recover_extraction(case_id: int, attempt_id: int, db: Session = Depends(get_db),
                       identity: Identity = Depends(require_permission("execute_ai"))):
    try:
        return extraction_attempts.recover(db,case_id,attempt_id,actor=identity.display_name,user_id=identity.user_id)
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc


class RetrieveDocument(BaseModel):
    request_key: UUID
    expected_url: str = Field(max_length=1000)


@router.get("/{case_id}/investigation/retrievals")
def retrievals(case_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    require_case(db, case_id)
    rows=db.scalars(select(RetrievalAttempt).where(RetrievalAttempt.case_id==case_id).order_by(RetrievalAttempt.id)).all()
    return {"policy":retrieval_attempts.POLICY,"provider":retrieval_attempts.provider_key(settings),
            "attempts":[retrieval_attempts.view(row) for row in rows]}


@router.post("/{case_id}/investigation/sources/{source_id}/retrieve")
async def retrieve(case_id: int, source_id: int, payload: RetrieveDocument, db: Session = Depends(get_db),
                   settings: Settings = Depends(get_settings), identity: Identity = Depends(require_permission("operate_sources"))):
    try:
        return await retrieval_attempts.execute(db,case_id,source_id,settings,request_key=payload.request_key,
            expected_url=payload.expected_url,actor=identity.display_name,user_id=identity.user_id)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409,str(exc)) from exc


@router.post("/{case_id}/investigation/retrievals/{attempt_id}/recover")
def recover_retrieval(case_id: int, attempt_id: int, db: Session = Depends(get_db),
                     identity: Identity = Depends(require_permission("operate_sources"))):
    try:
        return retrieval_attempts.recover(db,case_id,attempt_id,actor=identity.display_name,user_id=identity.user_id)
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc


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


PAIR_EXPLANATIONS = {
    "same_content_hash": "The retained content hashes match. Repeated content is not additional corroboration.",
    "shared_syndication_provenance": "Both records identify the same syndication group or original story.",
    "normalized_publisher_match": "The recorded publisher names match after normalization.",
    "no_shared_provenance_observed": "No shared content, publisher or syndication provenance was observed. Independent reporting has not been verified.",
    "missing_provenance": "Required content or publisher provenance is missing; independence is unknown.",
}


@router.get("/{case_id}/investigation/evidence/{evidence_id}/comparisons")
def comparisons(case_id: int, evidence_id: int, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    item = db.get(CaseEvidence, evidence_id)
    if item is None or item.case_id != case_id:
        raise HTTPException(404, "Evidence not found in this case")
    rows = db.scalars(select(CaseEvidence).where(CaseEvidence.case_id == case_id,
        CaseEvidence.id != evidence_id).order_by(CaseEvidence.id).offset((page-1)*20).limit(21)).all()
    results = []
    for other in rows[:20]:
        relationship, basis = evidence_relationship(item, other)
        rule = basis["rule"]
        # Legacy incomplete imports must not turn absent values into corroboration.
        # This read-only presentation does not alter stored relationships or scores.
        missing_hash = not item.content_hash.strip() or not other.content_hash.strip()
        missing_publisher = not normalize_identity(item.publisher) or not normalize_identity(other.publisher)
        if ((relationship == "duplicate" and missing_hash)
            or (relationship == "same_publisher" and missing_publisher)
            or (relationship == "independent" and (missing_hash or missing_publisher))):
            relationship, rule = "unknown", "missing_provenance"
        results.append({"evidence_id": other.id, "publisher": other.publisher, "url": other.canonical_url,
            "relationship": relationship, "rule": rule, "explanation": PAIR_EXPLANATIONS[rule]})
    return {"items": results, "has_next": len(rows)>20, "method": "evidence-pair-inspection-v1"}


class RecordCaseDecision(BaseModel):
    request_key: UUID
    decision: case_decisions.DecisionInput


@router.get('/{case_id}/decisions')
def decisions(case_id:int,page:int=Query(1,ge=1),db:Session=Depends(get_db)):
    require_case(db,case_id)
    rows=db.scalars(select(CaseDecision).where(CaseDecision.case_id==case_id).order_by(CaseDecision.id.desc()).offset((page-1)*10).limit(11)).all()
    current=case_decisions.latest(db,case_id)
    return {'items':[case_decisions.view(r) for r in rows[:10]],'has_next':len(rows)>10,
        'latest':case_decisions.view(current) if current else None}


@router.post('/{case_id}/decisions')
def record_decision(case_id:int,payload:RecordCaseDecision,db:Session=Depends(get_db),
                    identity:Identity=Depends(require_permission('review'))):
    try:
        return case_decisions.save(db,case_id,payload.decision,request_key=payload.request_key,
            actor=identity.display_name,actor_key=extraction_attempts.digest([identity.provider,identity.subject]),user_id=identity.user_id)
    except ValueError as exc:
        db.rollback();raise HTTPException(409,str(exc)) from exc


@router.get('/{case_id}/decisions/{decision_id}/development-brief')
def development_brief(case_id: int, decision_id: int, db: Session = Depends(get_db)):
    try:
        return development_briefs.handoff(db, case_id, decision_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post('/{case_id}/decisions/{decision_id}/development-brief/export')
def export_development_brief(case_id: int, decision_id: int, db: Session = Depends(get_db),
                             identity: Identity = Depends(require_permission('export'))):
    packet = development_brief(case_id, decision_id, db)
    content = development_briefs.text_export(packet)
    db.add(AuditEvent(actor=identity.display_name, user_id=identity.user_id,
        action='development_brief_exported', after_state={'case_id': case_id, 'decision_id': decision_id,
        'brief_id': packet['saved_brief']['id']}, detail='Internal reviewed text handoff downloaded; no communication sent.'))
    db.commit()
    return Response(content, media_type='text/plain', headers={
        'Content-Disposition': f'attachment; filename="dealsage-case-{case_id}-decision-{decision_id}.txt"',
        'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})
