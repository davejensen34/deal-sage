from copy import deepcopy
from uuid import uuid4
import asyncio
import pytest
from sqlalchemy import select,func
from app.domain.models import AuditEvent, ResearchQuery, CaseBriefVersion
from app.research import policy_renewal as service, followups, brief_versions
from app.research.discovery_runs import execute_attempt
from test_followups import make,config,settings

def test_renewal_preserves_history_budget_and_rejects_obsolete_plan(override_db_session,monkeypatch):
    db=override_db_session;case,run=make(db)
    old=deepcopy(run.plan);budget=deepcopy(case.research_budget)
    p=brief_versions.preview(db,case.id)
    saved=brief_versions.save(db,case.id,request_key=uuid4(),expected_hash=p['content_hash'],expected_version=0,actor='Reviewer',actor_key='reviewer')
    monkeypatch.setattr(service,'today',lambda:'2026-09-16')
    p=service.preview(db,case.id);args=dict(expected_hash=p['hash'],request_key=uuid4(),reason='Explicitly reassess the monitoring date window.',actor='Reviewer',actor_key='reviewer')
    r=service.save(db,case.id,**args)
    assert service.save(db,case.id,**args)==r
    assert case.signal_intake_policy['assessment_date']=='2026-09-16'
    assert case.research_budget==budget and run.plan==old
    assert db.get(CaseBriefVersion,saved['id']).content==saved['content']
    fresh=brief_versions.preview(db,case.id)
    assert not fresh['unchanged']
    assert fresh['content']['signal_intake_policy']==case.signal_intake_policy
    with pytest.raises(ValueError,match='date policy changed'):
        asyncio.run(execute_attempt(db,run,settings(),request_key=uuid4(),expected_revision=0,actor='Operator'))
    db.rollback()
    new=followups.preview(db,case.id,config(),settings())
    assert 'before:2026-09-17' in new['plan']['submitted_queries'][0]
    with pytest.raises(ValueError,match='different renewal'):service.save(db,case.id,**{**args,'reason':'A conflicting replacement reason.'})
    db.rollback()
    assert db.scalar(select(func.count(AuditEvent.id)).where(AuditEvent.action==service.ACTION,AuditEvent.after_state['case_id'].as_integer()==case.id))==1

def test_active_and_stale_renewal_denied_without_mutation(override_db_session,monkeypatch):
    db=override_db_session;case,_=make(db);monkeypatch.setattr(service,'today',lambda:'2026-09-16')
    p=service.preview(db,case.id);args=dict(expected_hash=p['hash'],request_key=uuid4(),reason='Refresh a retained research window.',actor='Reviewer',actor_key='reviewer')
    q=ResearchQuery(case_id=case.id,query_text='fixture',provider='fixture',max_results=1,status='running');db.add(q);db.commit()
    with pytest.raises(ValueError,match='active research'):service.save(db,case.id,**args)
    db.rollback();assert case.signal_intake_policy is None
    q.status='succeeded';db.commit();monkeypatch.setattr(service,'today',lambda:'2026-09-17')
    with pytest.raises(ValueError,match='date changed'):service.save(db,case.id,**args)
    db.rollback();assert case.signal_intake_policy is None

def test_policy_api_roles_and_safe_history(client,override_db_session,monkeypatch):
    from app.main import app
    from app.auth.service import current_identity,Identity
    db=override_db_session;case,_=make(db);role='viewer'
    monkeypatch.setattr(service,'today',lambda:'2026-09-16')
    app.dependency_overrides[current_identity]=lambda:Identity(None,'demo','test',None,'Named reviewer',role=role)
    url=f'/api/followups/cases/{case.id}/date-policy'
    try:
        p=client.get(url).json();body=dict(request_key=str(uuid4()),expected_hash=p['hash'],reason='Explicit monitoring policy renewal.')
        assert client.post(url,json=body).status_code==403
        role='analyst';assert client.post(url,json=body).status_code==200
        h=client.get(url).json()['history'];assert h[0]['actor']=='Named reviewer' and 'actor_key' not in h[0]
        assert not client.get(url).json()['changed']
    finally:app.dependency_overrides.pop(current_identity,None)


def test_obsolete_discovery_rejected_before_any_reservation(override_db_session,monkeypatch):
    from test_discovery_runs import make as discovery
    from app.domain.models import DiscoveryAttempt, ResearchCase
    db=override_db_session;run=discovery(db)
    case=db.get(ResearchCase,run.case_id)
    old=deepcopy(run.plan)
    monkeypatch.setattr(service,'today',lambda:'2026-09-17')
    p=service.preview(db,case.id)
    service.save(db,case.id,expected_hash=p['hash'],request_key=uuid4(),
        reason='Explicit current monitoring window.',actor='Reviewer',actor_key='reviewer')
    with pytest.raises(ValueError,match='date policy changed'):
        asyncio.run(execute_attempt(db,run,settings(),request_key=uuid4(),expected_revision=0,actor='Operator'))
    db.rollback()
    assert run.plan==old and run.reserved_cents==0
    assert db.scalar(select(func.count(DiscoveryAttempt.id)).where(DiscoveryAttempt.run_id==run.id))==0
