from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.openai import OpenAIProvider
from app.auth.service import Identity, current_identity
from app.core.config import get_settings
from app.core.database import get_db
from app.domain.models import AIExecution, AcquisitionRun, AuditEvent, Business, CandidateMatch, CaseEvidence, CuratedRecord, Evidence, EvidenceClaim, Person, RawArtifact, ResearchCase, ResearchFrontierItem, ResearchInference, ResearchQuery, ResearchStage, ResearchStep, ResearchTrail, ReviewCase, RunArtifact, SignalResolution, SourceCandidate, TransitionSignal
from app.domain.research import funnel_counts
from app.domain.schemas import CandidatePage, NoteCreate, StatusUpdate
from app.research.sources.colorado import ColoradoBusinessEntitiesAdapter
from app.research.sources.texas import TexasActiveFranchiseTaxpayersAdapter
from app.research.sources.utah import UTAH_BEL_DEFINITION

router = APIRouter(prefix="/api", dependencies=[Depends(current_identity)])
settings = get_settings()


def item(c: CandidateMatch) -> dict:
    return {"id":c.id,"business":c.business.legal_name,"owner":c.person.full_name,"city":c.business.city,"state":c.business.state,"signal_type":c.signal.signal_type,"transition_date":c.signal.possible_transition_date,"owner_business_confidence":c.owner_business_confidence,"signal_identity_confidence":c.signal_identity_confidence,"overall_candidate_confidence":c.overall_candidate_confidence,"status":c.status,"updated_at":c.updated_at}


@router.get("/health")
def health(): return {"status":"ok"}


@router.get("/research/sources")
def research_sources():
    """Expose source contracts without initiating network acquisition."""
    definitions=(ColoradoBusinessEntitiesAdapter.definition,TexasActiveFranchiseTaxpayersAdapter.definition,UTAH_BEL_DEFINITION)
    return [{**asdict(definition),"contract_fingerprint":definition.contract_fingerprint} for definition in definitions]


@router.get("/research/acquisition-runs")
def acquisition_runs(db: Session = Depends(get_db)):
    """Expose operational outcomes without leaking raw content or request secrets."""
    runs = db.scalars(select(AcquisitionRun).order_by(AcquisitionRun.started_at.desc())).all()
    result=[]
    for run in runs:
        artifact_ids=select(RunArtifact.artifact_id).where(RunArtifact.run_id==run.id)
        result.append({"id":run.id,"source_key":run.source_key,"jurisdiction":run.jurisdiction,"discovery_strategy":run.discovery_strategy,"status":run.status,"started_at":run.started_at,"finished_at":run.finished_at,"metrics":run.metrics,"artifact_count":db.scalar(select(func.count(RawArtifact.id)).where(RawArtifact.id.in_(artifact_ids))) or 0,"curated_count":db.scalar(select(func.count(CuratedRecord.id)).where(CuratedRecord.artifact_id.in_(artifact_ids),CuratedRecord.status=="curated")) or 0,"quarantined_count":db.scalar(select(func.count(CuratedRecord.id)).where(CuratedRecord.artifact_id.in_(artifact_ids),CuratedRecord.status=="quarantined")) or 0})
    return result


@router.get("/research/resolution-outcomes")
def resolution_outcomes(db: Session = Depends(get_db)):
    """Expose aggregate signal-first outcomes without person or business identifiers."""
    rows = db.execute(
        select(SignalResolution.outcome, func.count(SignalResolution.id)).group_by(
            SignalResolution.outcome
        )
    ).all()
    counts = {outcome: count for outcome, count in rows}
    return {
        "total": sum(counts.values()),
        "outcomes": [
            {"outcome": outcome, "count": counts.get(outcome, 0)}
            for outcome in (
                "pending",
                "business_resolved",
                "no_business_found",
                "relationship_unknown",
            )
        ],
    }


@router.get("/research/case-metrics")
def research_case_metrics(db: Session = Depends(get_db)):
    """Expose convergence volumes without returning case evidence or claims."""
    strategy_rows = db.execute(
        select(ResearchCase.origin_strategy, func.count(ResearchCase.id)).group_by(
            ResearchCase.origin_strategy
        )
    ).all()
    return {
        "cases": db.scalar(select(func.count(ResearchCase.id))) or 0,
        "evidence_items": db.scalar(select(func.count(CaseEvidence.id))) or 0,
        "claims": db.scalar(select(func.count(EvidenceClaim.id))) or 0,
        "inferences": db.scalar(select(func.count(ResearchInference.id))) or 0,
        "search_queries": db.scalar(select(func.count(ResearchQuery.id))) or 0,
        "source_candidates": db.scalar(select(func.count(SourceCandidate.id))) or 0,
        "promoted_sources": db.scalar(
            select(func.count(SourceCandidate.id)).where(
                SourceCandidate.status == "promoted"
            )
        ) or 0,
        "frontier_items": db.scalar(select(func.count(ResearchFrontierItem.id))) or 0,
        "research_steps": db.scalar(select(func.count(ResearchStep.id))) or 0,
        "stopped_cases": db.scalar(
            select(func.count(ResearchCase.id)).where(ResearchCase.status == "stopped")
        ) or 0,
        "by_origin_strategy": {
            strategy: count for strategy, count in strategy_rows
        },
    }


@router.get("/research/experiments/colorado-owner-discovery")
def colorado_owner_discovery_result():
    result_path = Path(__file__).parents[1] / "research/results/colorado_owner_discovery_summary.json"
    if not result_path.exists():
        raise HTTPException(503, "The Colorado experiment result has not been recorded yet")
    return json.loads(result_path.read_text())


@router.get("/research/experiments/milestone3-source-samples")
def milestone3_source_samples_result():
    """Serve committed aggregate results without exposing raw source records."""
    result_path = (
        Path(__file__).parents[1]
        / "research/results/milestone3_source_samples_summary.json"
    )
    if not result_path.exists():
        raise HTTPException(503, "The Milestone 3 sample result has not been recorded yet")
    return json.loads(result_path.read_text())


@router.get("/research/funnel")
def research_funnel(db: Session = Depends(get_db)):
    return funnel_counts(db.scalars(select(ResearchStage)).all())


@router.get("/research/trails/{business_id}")
def research_trail(business_id: int, db: Session = Depends(get_db)):
    trail = db.scalar(select(ResearchTrail).where(ResearchTrail.business_id == business_id).options(selectinload(ResearchTrail.business), selectinload(ResearchTrail.target_profile), selectinload(ResearchTrail.stages).selectinload(ResearchStage.source)))
    if not trail: raise HTTPException(404, "Research trail not found")
    return {"id":trail.id,"business":{"id":trail.business.id,"name":trail.business.legal_name},"target_profile":{"name":trail.target_profile.name,"criteria":trail.target_profile.criteria,"provenance":trail.target_profile.provenance} if trail.target_profile else None,"owner_research_ready":trail.owner_research_ready,"readiness_explanation":trail.readiness_explanation,"stages":[{"id":s.id,"type":s.stage_type,"sequence":s.sequence,"status":s.status,"confidence":s.confidence,"detail":s.detail,"supporting_evidence":s.supporting_evidence,"contradictions":s.contradictions,"missing_evidence":s.missing_evidence,"evidence_refs":s.evidence_refs,"person_id":s.person_id,"relationship_id":s.relationship_id,"source":{"publisher":s.source.publisher,"canonical_url":s.source.canonical_url,"retrieved_at":s.source.retrieved_at,"classification":"source_fact"} if s.source else None} for s in trail.stages]}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    candidates = db.scalars(select(CandidateMatch).options(selectinload(CandidateMatch.business), selectinload(CandidateMatch.person), selectinload(CandidateMatch.signal)).order_by(CandidateMatch.updated_at.desc())).all()
    counts = {status: sum(c.status==status for c in candidates) for status in ["new","researching","needs_review","validated","rejected","watchlist"]}
    states: dict[str,int] = {}
    for c in candidates: states[c.business.state or "Unknown"] = states.get(c.business.state or "Unknown",0)+1
    audits = db.scalars(select(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(8)).all()
    return {"metrics":{"total":len(candidates),"new":counts["new"],"needs_review":counts["needs_review"],"validated":counts["validated"],"high_confidence":sum(c.overall_candidate_confidence>=80 for c in candidates),"rejected":counts["rejected"],"average_confidence":round(sum(c.overall_candidate_confidence for c in candidates)/len(candidates)),"evidence_items":db.scalar(select(func.count(Evidence.id)))},"status_distribution":[{"name":k.replace("_"," ").title(),"value":v} for k,v in counts.items()],"geography":[{"state":k,"candidates":v} for k,v in states.items()],"confidence_distribution":[{"range":label,"value":sum(lo<=c.overall_candidate_confidence<=hi for c in candidates)} for label,lo,hi in [("0–39",0,39),("40–59",40,59),("60–79",60,79),("80–100",80,100)]],"recent_candidates":[item(c) for c in candidates[:6]],"recent_activity":[{"id":a.id,"action":a.action,"actor":a.actor,"timestamp":a.timestamp,"detail":a.detail,"candidate_id":a.candidate_id} for a in audits]}


@router.get("/candidates", response_model=CandidatePage)
def candidates(q: str|None=None,status: str|None=None,state: str|None=None,signal: str|None=None,min_confidence: int=0,sort: str="updated",order: str="desc",page: int=Query(1,ge=1),page_size: int=Query(10,ge=1,le=100),db: Session=Depends(get_db)):
    stmt=select(CandidateMatch).join(CandidateMatch.business).join(CandidateMatch.person).join(CandidateMatch.signal).options(selectinload(CandidateMatch.business),selectinload(CandidateMatch.person),selectinload(CandidateMatch.signal))
    if q: stmt=stmt.where(or_(Business.legal_name.ilike(f"%{q}%"),Person.first_name.ilike(f"%{q}%"),Person.last_name.ilike(f"%{q}%")))
    if status: stmt=stmt.where(CandidateMatch.status==status)
    if state: stmt=stmt.where(Business.state==state)
    if signal: stmt=stmt.where(CandidateMatch.signal.has(signal_type=signal))
    stmt=stmt.where(CandidateMatch.overall_candidate_confidence>=min_confidence)
    total=db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    sort_col={"business":Business.legal_name,"owner":Person.last_name,"confidence":CandidateMatch.overall_candidate_confidence,"status":CandidateMatch.status,"updated":CandidateMatch.updated_at}.get(sort,CandidateMatch.updated_at)
    stmt=stmt.order_by(sort_col.asc() if order=="asc" else sort_col.desc()).offset((page-1)*page_size).limit(page_size)
    return {"items":[item(c) for c in db.scalars(stmt).all()],"total":total,"page":page,"page_size":page_size}


def load_candidate(candidate_id: int, db: Session) -> CandidateMatch:
    c=db.scalar(select(CandidateMatch).where(CandidateMatch.id==candidate_id).options(selectinload(CandidateMatch.business),selectinload(CandidateMatch.person),selectinload(CandidateMatch.relationship_record),selectinload(CandidateMatch.signal).selectinload(TransitionSignal.source),selectinload(CandidateMatch.evidence).selectinload(Evidence.source)))
    if not c: raise HTTPException(404,"Candidate not found")
    return c


@router.get("/candidates/{candidate_id}")
def detail(candidate_id:int,db:Session=Depends(get_db),identity:Identity=Depends(current_identity)):
    c=load_candidate(candidate_id,db)
    review=db.scalar(select(ReviewCase).where(ReviewCase.candidate_id==candidate_id))
    audits=db.scalars(select(AuditEvent).where(AuditEvent.candidate_id==candidate_id).order_by(AuditEvent.timestamp.desc())).all()
    db.add(AuditEvent(candidate_id=c.id,user_id=identity.user_id,actor=identity.display_name,action="candidate_viewed",detail="Candidate detail reviewed.")); db.commit()
    source=lambda s:{"id":s.id,"source_type":s.source_type,"publisher":s.publisher,"canonical_url":s.canonical_url,"published_at":s.published_at,"retrieved_at":s.retrieved_at,"reliability":s.reliability,"is_demo":s.is_demo}
    return {"id":c.id,"business":{k:getattr(c.business,k) for k in ["id","legal_name","doing_business_as","status","industry","website","address","city","state","postal_code","registration_number","employee_range","revenue_range"]},"person":{"id":c.person.id,"full_name":c.person.full_name,"aliases":c.person.aliases,"approximate_birth_year":c.person.approximate_birth_year,"city":c.person.city,"state":c.person.state},"relationship":{k:getattr(c.relationship_record,k) for k in ["relationship_type","start_date","end_date","active","confidence"]},"signal":{"signal_type":c.signal.signal_type,"published_name":c.signal.published_name,"possible_transition_date":c.signal.possible_transition_date,"publication_date":c.signal.publication_date,"city":c.signal.city,"state":c.signal.state,"age":c.signal.age,"relatives":c.signal.relatives,"occupation_clues":c.signal.occupation_clues,"business_clues":c.signal.business_clues,"extraction_confidence":c.signal.extraction_confidence,"source":source(c.signal.source)},"scores":{"business_relationship":c.owner_business_confidence,"signal_identity":c.signal_identity_confidence,"overall_candidate":c.overall_candidate_confidence},"status":c.status,"match_explanation":c.match_explanation,"positive_signals":c.positive_signals,"conflicting_signals":c.conflicting_signals,"missing_evidence":c.missing_evidence,"recommended_next_action":c.recommended_next_action,"last_researched_at":c.last_researched_at,"evidence":[{"id":e.id,"evidence_type":e.evidence_type,"extracted_text":e.extracted_text,"normalized_facts":e.normalized_facts,"extractor_type":e.extractor_type,"model_used":e.model_used,"retrieved_at":e.retrieved_at,"evidence_strength":e.evidence_strength,"explanation":e.explanation,"classification":e.classification,"source":source(e.source)} for e in c.evidence],"review":{"assigned_user":review.assigned_user,"status":review.status,"decision":review.decision,"analyst_notes":review.analyst_notes,"decision_reason_codes":review.decision_reason_codes,"reviewed_at":review.reviewed_at} if review else None,"audit":[{"id":a.id,"actor":a.actor,"timestamp":a.timestamp,"action":a.action,"detail":a.detail,"before_state":a.before_state,"after_state":a.after_state} for a in audits]}


@router.patch("/candidates/{candidate_id}/status")
def update_status(candidate_id:int,payload:StatusUpdate,db:Session=Depends(get_db),identity:Identity=Depends(current_identity)):
    c=load_candidate(candidate_id,db); before=c.status; c.status=payload.status
    review=db.scalar(select(ReviewCase).where(ReviewCase.candidate_id==candidate_id)); now=datetime.now(timezone.utc)
    if review:
        review.status="closed" if payload.status in {"validated","rejected"} else "open"; review.decision=payload.status; review.reviewed_at=now; review.decision_reason_codes=[payload.reason]; review.analyst_notes=[*(review.analyst_notes or []),{"note":payload.note,"author":identity.display_name,"user_id":identity.user_id,"timestamp":now.isoformat()}]
    db.add(AuditEvent(candidate_id=c.id,user_id=identity.user_id,actor=identity.display_name,action="status_changed",before_state={"status":before},after_state={"status":payload.status},detail=f"{payload.reason}: {payload.note}")); db.commit()
    return {"id":c.id,"status":c.status}


@router.post("/candidates/{candidate_id}/notes")
def add_note(candidate_id:int,payload:NoteCreate,db:Session=Depends(get_db),identity:Identity=Depends(current_identity)):
    load_candidate(candidate_id,db); review=db.scalar(select(ReviewCase).where(ReviewCase.candidate_id==candidate_id)); now=datetime.now(timezone.utc)
    note={"note":payload.note,"author":identity.display_name,"user_id":identity.user_id,"timestamp":now.isoformat()}; review.analyst_notes=[*(review.analyst_notes or []),note]
    db.add(AuditEvent(candidate_id=candidate_id,user_id=identity.user_id,actor=identity.display_name,action="analyst_note_added",after_state=note,detail=payload.note)); db.commit(); return note


@router.get("/businesses")
def businesses(db:Session=Depends(get_db)): return db.scalars(select(Business).order_by(Business.legal_name)).all()
@router.get("/people")
def people(db:Session=Depends(get_db)): return [{"id":p.id,"name":p.full_name,"city":p.city,"state":p.state} for p in db.scalars(select(Person)).all()]
@router.get("/evidence")
def evidence(db:Session=Depends(get_db)): return [{"id":e.id,"candidate_id":e.candidate_id,"type":e.evidence_type,"strength":e.evidence_strength,"classification":e.classification,"publisher":e.source.publisher,"retrieved_at":e.retrieved_at} for e in db.scalars(select(Evidence).options(selectinload(Evidence.source)).order_by(Evidence.retrieved_at.desc())).all()]
@router.get("/activity")
def activity(db:Session=Depends(get_db)): return [{"id":a.id,"candidate_id":a.candidate_id,"actor":a.actor,"timestamp":a.timestamp,"action":a.action,"detail":a.detail} for a in db.scalars(select(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(100)).all()]


@router.post("/candidates/{candidate_id}/ai-summary")
async def ai_summary(candidate_id:int,db:Session=Depends(get_db)):
    c=load_candidate(candidate_id,db); provider=None
    if settings.model_provider=="openai" and settings.openai_api_key: provider=OpenAIProvider(settings.openai_api_key,settings.openai_model); model=settings.openai_model
    elif settings.model_provider=="anthropic" and settings.anthropic_api_key: provider=AnthropicProvider(settings.anthropic_api_key,settings.anthropic_model); model=settings.anthropic_model
    else: raise HTTPException(503,"AI summaries are disabled. Configure a provider and API key.")
    prompt=Path(__file__).parents[1]/"ai/prompts/candidate_summary_v1.txt"; context=prompt.read_text()+"\n\n"+str({"candidate":item(c),"evidence":[e.extracted_text for e in c.evidence],"conflicts":c.conflicting_signals,"missing":c.missing_evidence})
    start=perf_counter()
    try: summary=await provider.summarize(context); ok=True; error=None
    except Exception as exc: summary=""; ok=False; error=str(exc)
    db.add(AIExecution(candidate_id=c.id,provider=settings.model_provider,model=model,prompt_version="candidate-summary-v1",latency_ms=int((perf_counter()-start)*1000),success=ok,error=error)); db.commit()
    if not ok: raise HTTPException(502,"AI provider request failed")
    return {"label":"AI Research Summary","summary":summary,"provider":settings.model_provider,"model":model,"prompt_version":"candidate-summary-v1"}
