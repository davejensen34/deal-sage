"""Explicit one-document authorizations, independent of frozen discovery plans."""
import asyncio
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit
from uuid import UUID

from sqlalchemy import select, update

from app.domain.models import AuditEvent, ResearchCase, RetrievalAttempt, SourceCandidate
from app.research.discovery_runs import utc
from app.research.retrieval import (BLOCKING_ACCESS_FLAGS, CandidateRetrievalService, FixtureDocumentProvider,
    HttpDocumentProvider, RetrievedDocument, assert_nonlocal_url)
from app.storage.local import LocalEvidenceStorage

POLICY = {"version": "case-document-v1", "max_bytes": 1_000_000, "timeout_seconds": 20,
          "max_redirects": 0, "automatic_retries": 0, "documents": 1,
          "max_source_attempts": 3, "max_case_attempts": 20, "provider_cost_cents": 0}


def provider_key(settings):
    # A demo must never accidentally turn a real source URL into fixture evidence.
    return "fixture" if settings.demo_mode else "public_http"


def view(row):
    return {"id": row.id, "source_id": row.source_id, "status": row.status, "actor": row.actor,
        "plan": row.plan, "evidence_id": row.evidence_id, "error_code": row.error_code,
        "recovery_after": utc(row.recovery_after), "created_at": utc(row.created_at)}


async def execute(db, case_id, source_id, settings, *, request_key, expected_url, actor, user_id=None, provider=None, storage=None):
    key = str(UUID(str(request_key)))
    # Serialize admission per case, including requests from separate workers.
    # The lock is released at reservation commit, never held over network I/O.
    locked = db.execute(update(ResearchCase).where(ResearchCase.id==case_id).values(updated_at=ResearchCase.updated_at))
    if locked.rowcount != 1:
        db.rollback(); raise ValueError("Research case not found")
    prior = db.scalar(select(RetrievalAttempt).where(RetrievalAttempt.request_key==key))
    if prior:
        if prior.case_id!=case_id or prior.source_id!=source_id or prior.actor!=actor or prior.plan["url"]!=expected_url:
            db.rollback(); raise ValueError("Request key belongs to another retrieval")
        result=view(prior); db.commit(); return result
    source=db.get(SourceCandidate,source_id)
    case=db.get(ResearchCase,case_id)
    db.refresh(case)
    if source is None or source.case_id!=case_id:
        db.rollback(); raise ValueError("Source not found in this case")
    db.refresh(source)
    if case.status!="open" or source.canonical_url!=expected_url:
        db.rollback(); raise ValueError("Case is stopped or source changed; reload before retrieval")
    if source.access_decision!="approved" or any(source.access_observations.get(f) is True for f in BLOCKING_ACCESS_FLAGS):
        db.rollback(); raise ValueError("Source access approval is missing or restricted")
    attempts=db.scalars(select(RetrievalAttempt).where(RetrievalAttempt.case_id==case_id)).all()
    if any(a.status=="running" for a in attempts):
        db.rollback(); raise ValueError("A retrieval is active; reload or recover its interrupted outcome")
    if len(attempts)>=POLICY["max_case_attempts"] or sum(a.source_id==source_id for a in attempts)>=POLICY["max_source_attempts"]:
        db.rollback(); raise ValueError("Retrieval attempt ceiling exhausted")
    assert_nonlocal_url(expected_url)
    mode=provider_key(settings)
    if mode=="fixture":
        url=urlsplit(expected_url)
        if not (settings.auth_mode=="demo" and url.hostname=="example.test" and url.path.startswith("/fictional-discovery/")):
            db.rollback(); raise ValueError("Demo retrieval supports only explicit fictional discovery URLs")
    now=datetime.now(timezone.utc)
    row=RetrievalAttempt(request_key=key,case_id=case_id,source_id=source_id,actor=actor,
        plan={**POLICY,"url":expected_url,"provider":mode},recovery_after=now+timedelta(seconds=80))
    db.add(row)
    db.add(AuditEvent(actor=actor,user_id=user_id,action="retrieval_authorized",
        after_state={"case_id":case_id,"source_candidate_id":source_id,"request_key":key,"policy":POLICY["version"]},
        detail="Authorized one bounded source retrieval; discovery limits unchanged."))
    db.commit(); db.refresh(row)
    if provider is None:
        provider = FixtureDocumentProvider(RetrievedDocument(expected_url,
            ("Fictional demonstration document for " + expected_url + ". A business transition is unverified; ownership and financials are unknown.").encode(),
            "text/plain", now)) if mode=="fixture" else HttpDocumentProvider(timeout_seconds=20,max_redirects=0)
    deadline=now+timedelta(seconds=20)

    def accept_results():
        # Hold this fence through all SQL landing writes and the final outcome.
        # Recovery that wins first prevents a late response from publishing evidence.
        if datetime.now(timezone.utc)>deadline:
            raise TimeoutError()
        accepted=db.execute(update(RetrievalAttempt).where(RetrievalAttempt.id==row.id,
            RetrievalAttempt.status=="running").values(status="running"))
        if accepted.rowcount!=1:
            raise ValueError("Attempt was recovered; late response rejected")

    try:
        evidence=await asyncio.wait_for(CandidateRetrievalService(db,storage or LocalEvidenceStorage(settings.evidence_storage_path),
            defer_commit=True).retrieve(case_id,source_id,provider,max_bytes=POLICY["max_bytes"],
                authorization_id=row.id,accept_results=accept_results),timeout=20)
        row.evidence_id=evidence.id; row.status="succeeded"
        db.add(AuditEvent(actor=actor,user_id=user_id,action="retrieval_completed",
            after_state={"case_id":case_id,"attempt_id":row.id,"evidence_id":evidence.id},
            detail="Retained source evidence; no claim validation or model call."))
        db.commit()
    except Exception as exc:
        db.rollback()
        # A recovered unknown outcome must not be overwritten by the old worker.
        db.execute(update(RetrievalAttempt).where(RetrievalAttempt.id==row.id,RetrievalAttempt.status=="running")
            .values(status="failed",error_code="timeout" if isinstance(exc,TimeoutError) else "retrieval_failed"))
        db.commit()
    # Cancellation/process death intentionally retains a running authorization.
    db.refresh(row)
    return view(row)


def recover(db, case_id, attempt_id, *, actor, user_id=None):
    row=db.get(RetrievalAttempt,attempt_id)
    if row is None or row.case_id!=case_id:
        raise ValueError("Retrieval attempt not found in this case")
    if datetime.now(timezone.utc)<utc(row.recovery_after):
        raise ValueError("Recovery is not available until the request timeout and grace period expire")
    changed=db.execute(update(RetrievalAttempt).where(RetrievalAttempt.id==attempt_id,RetrievalAttempt.status=="running")
        .values(status="unknown",error_code="interrupted_outcome_unknown"))
    if changed.rowcount!=1:
        db.rollback(); raise ValueError("Attempt already finished; reload its outcome")
    db.add(AuditEvent(actor=actor,user_id=user_id,action="retrieval_recovered",
        after_state={"case_id":case_id,"attempt_id":attempt_id},detail="Retained unknown retrieval outcome; no automatic replay."))
    db.commit(); db.refresh(row)
    return view(row)
