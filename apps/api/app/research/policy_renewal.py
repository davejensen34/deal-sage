"""Explicit date-window renewal; historical evidence and plans stay frozen."""
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select, update
from app.domain.models import (ResearchCase, AuditEvent, DiscoveryRun, FollowupRun,
    RetrievalAttempt, ExtractionAttempt, ResearchQuery, ResearchStep)
from app.research.signal_freshness import validate_policy
from app.research.discovery_runs import digest

ACTION='case_date_policy_renewed'

def today():
    return datetime.now(timezone.utc).date().isoformat()

def history_query(case_id):
    return select(AuditEvent).where(AuditEvent.action==ACTION,
        AuditEvent.after_state['case_id'].as_integer()==case_id)

def preview(db,case_id):
    case=db.get(ResearchCase,case_id)
    if case is None or case.status!='open': raise ValueError('An open case is required')
    before=validate_policy(case.signal_intake_policy) if case.signal_intake_policy is not None else None
    after=validate_policy({'version':'signal-intake-v1','assessment_date':today(),
        'lookback_days':before['lookback_days'] if before else 90})
    plan={'case_id':case_id,'before':before,'after':after}
    return {**plan,'hash':digest(plan),'changed':before!=after}

def save(db,case_id,*,expected_hash,request_key,reason,actor,actor_key,user_id=None):
    key=str(UUID(str(request_key)))
    if not 10<=len(reason.strip())<=1000: raise ValueError('Explain renewal in 10 to 1000 characters')
    claim=db.execute(update(ResearchCase).where(ResearchCase.id==case_id).values(updated_at=ResearchCase.updated_at))
    if claim.rowcount!=1: raise ValueError('Case not found')
    # The case lock serializes same-case UUID retries and policy changes. Audit
    # history is the durable before/after record; no historical plan is edited.
    prior=db.scalar(history_query(case_id).where(AuditEvent.after_state['request_key'].as_string()==key))
    if prior:
        a=prior.after_state
        if (a['expected_hash'],a['actor_key'],prior.detail)!=(expected_hash,actor_key,reason.strip()):
            raise ValueError('Request key belongs to a different renewal')
        db.commit();return {'id':prior.id,'before':prior.before_state,'after':a['policy']}
    db.expire_all();p=preview(db,case_id)
    if p['hash']!=expected_hash: raise ValueError('Policy or date changed; preview again')
    if not p['changed']: raise ValueError('The case already uses the current date window')
    for model in (DiscoveryRun,FollowupRun,RetrievalAttempt,ExtractionAttempt,ResearchQuery,ResearchStep):
        if db.scalar(select(model.id).where(model.case_id==case_id,model.status=='running').limit(1)):
            raise ValueError('Finish or recover active research before renewing the date window')
    case=db.get(ResearchCase,case_id);case.signal_intake_policy=p['after']
    row=AuditEvent(actor=actor,user_id=user_id,action=ACTION,before_state=p['before'],
        after_state={'case_id':case_id,'request_key':key,'expected_hash':expected_hash,
                     'actor_key':actor_key,'policy':p['after']},detail=reason.strip())
    db.add(row);db.commit();db.refresh(row)
    return {'id':row.id,'before':p['before'],'after':p['after']}
