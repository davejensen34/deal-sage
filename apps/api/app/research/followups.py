"""Reviewer-authored follow-up searches with their own frozen authorization."""
from datetime import datetime, timezone
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update, func
from app.domain.models import (ResearchCase, ResearchFrontierItem, ResearchStep,
    FollowupRun, FollowupAttempt, SourceCandidate, AuditEvent)
from app.research.discovery_runs import digest, provider_snapshot, run_view
from app.research.signal_freshness import dated_query
from app.research.search_openai import search_request


class FollowupSettings(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    question: str = Field(min_length=10, max_length=500)
    rationale: str = Field(min_length=10, max_length=1000)
    query: str = Field(min_length=5, max_length=350)


def preview(db, case_id, config, settings):
    case=db.get(ResearchCase,case_id)
    if case is None or case.status!='open':
        raise ValueError('Follow-up requires an open case')
    if any(not v.strip() for v in config.model_dump().values()):
        raise ValueError('Question, rationale and query must contain text')
    today=datetime.now(timezone.utc).date()
    policy=case.signal_intake_policy or {'assessment_date':today.isoformat(),'lookback_days':90}
    submitted=dated_query(config.query.strip(),case.signal_intake_policy)
    if len(submitted)>500: raise ValueError('Dated query exceeds 500 characters')
    count=db.scalar(select(func.count(SourceCandidate.id)).where(SourceCandidate.case_id==case_id)) or 0
    provider=provider_snapshot(settings,today)
    plan={'version':'case-followup-v1','case_id':case_id,'question':config.question.strip(),
        'rationale':config.rationale.strip(),'input':config.model_dump(),
        'settings':{'objective':config.question.strip(),'max_queries':2,'max_records':min(100,count+10),
            'max_cost_cents':24,'max_elapsed_seconds':600,'lookback_days':policy['lookback_days']},
        'policy':policy,'provider':provider,'queries':[config.query.strip()],
        'submitted_queries':[submitted],'requests':[search_request(submitted,provider['model'],provider['max_output_tokens'])] if provider['key']=='openai' else [],
        'provider_retries':0,'retrieval_calls':0,'analysis_calls':0}
    return {'plan':plan,'hash':digest(plan)}


def create(db,case_id,config,settings,*,request_key,expected_hash,actor,actor_key,user_id=None):
    key=str(UUID(str(request_key)))
    locked=db.execute(update(ResearchCase).where(ResearchCase.id==case_id).values(updated_at=ResearchCase.updated_at))
    if locked.rowcount!=1: raise ValueError('Case not found')
    existing=db.scalar(select(FollowupRun).where(FollowupRun.request_key==key))
    if existing:
        if (existing.case_id,existing.actor_key,existing.plan_hash,existing.plan['input'])!=(case_id,actor_key,expected_hash,config.model_dump()):
            raise ValueError('Request key belongs to another follow-up')
        db.commit();return existing
    db.expire_all()
    if (db.scalar(select(func.count(FollowupRun.id)).where(FollowupRun.case_id==case_id)) or 0)>=10:
        raise ValueError('Case ceiling of ten follow-up plans reached')
    prepared=preview(db,case_id,config,settings)
    if prepared['hash']!=expected_hash: raise ValueError('Case or plan changed; preview again')
    item=ResearchFrontierItem(case_id=case_id,question_type='find_independent_evidence',
        question=prepared['plan']['question'],rationale=prepared['plan']['rationale'],priority=50,max_attempts=2)
    db.add(item);db.flush()
    run=FollowupRun(case_id=case_id,frontier_id=item.id,request_key=key,actor=actor,actor_key=actor_key,
        plan=prepared['plan'],plan_hash=expected_hash)
    db.add(run);db.flush()
    db.add(AuditEvent(actor=actor,user_id=user_id,action='followup_created',after_state={
        'case_id':case_id,'frontier_id':item.id,'run_id':run.id},detail=item.rationale))
    db.commit();db.refresh(run);return run


def admit(db,run):
    # Serialize all follow-up admissions for this case, including different plans.
    locked=db.execute(update(ResearchCase).where(ResearchCase.id==run.case_id,
        ResearchCase.status=='open').values(updated_at=ResearchCase.updated_at))
    if locked.rowcount!=1: raise ValueError('Case is stopped; follow-up unavailable')
    db.expire_all()
    item=db.get(ResearchFrontierItem,run.frontier_id)
    if item is None or item.case_id!=run.case_id or item.status!='pending' or item.attempts>=item.max_attempts:
        raise ValueError('Follow-up question is active, changed or exhausted')
    running=db.scalar(select(func.count(FollowupRun.id)).where(FollowupRun.case_id==run.case_id,FollowupRun.status=='running')) or 0
    if running: raise ValueError('Another follow-up is active; finish or recover it first')
    attempts=db.scalar(select(func.count(FollowupAttempt.id)).join(FollowupRun).where(FollowupRun.case_id==run.case_id)) or 0
    reserved=db.scalar(select(func.sum(FollowupRun.reserved_cents)).where(FollowupRun.case_id==run.case_id)) or 0
    if attempts>=20 or reserved+run.plan['provider']['reservation_cents']>240:
        raise ValueError('Case follow-up attempt or reservation ceiling exhausted')
    case=db.get(ResearchCase,run.case_id)
    if dated_query(run.plan['queries'][0],case.signal_intake_policy)!=run.plan['submitted_queries'][0]:
        raise ValueError('Case date policy changed; prepare a new follow-up')


def start(db,run,actor):
    item=db.get(ResearchFrontierItem,run.frontier_id)
    item.attempts+=1;item.status='in_progress'
    number=(db.scalar(select(func.max(ResearchStep.step_number)).where(ResearchStep.case_id==run.case_id)) or 0)+1
    step=ResearchStep(case_id=run.case_id,frontier_item_id=item.id,step_number=number,
        action_type='search',provider=run.plan['provider']['key'],cost_cents=run.plan['provider']['reservation_cents'])
    db.add(step);db.flush()
    db.add(AuditEvent(actor=actor,action='followup_reserved',after_state={'case_id':run.case_id,
        'run_id':run.id,'step_id':step.id,'reserved_cents':step.cost_cents},detail='Explicit follow-up search; no question resolution or evidence acceptance.'))
    return step.id


def finish(db,run,attempt):
    step=db.get(ResearchStep,attempt.step_id)
    item=db.get(ResearchFrontierItem,run.frontier_id)
    step.status=attempt.status;step.finished_at=datetime.now(timezone.utc)
    step.result_summary={'followup_run_id':run.id,'result_count':attempt.result_count,'question_resolved':False}
    # Finding a link, including a repeated link, never answers the research question.
    item.status='blocked' if item.attempts>=item.max_attempts else 'pending'
