from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from app.domain.models import CaseMonitoring, AuditEvent
from app.research.cases import ResearchCaseService
from app.research import case_monitoring as service


def plan(**changes):
    return service.MonitoringInput(**{'expected_prior_id': None, 'due_on': '2026-09-15',
        'state': 'active', 'question': 'Has independent business identity evidence become available?',
        'reason': 'Retain this unresolved lead for a manual review.', **changes})


def save(db, case, payload=None, key=None, owner='reviewer'):
    return service.save(db, case.id, payload or plan(), request_key=key or uuid4(), owner_key=owner, actor='Reviewer')


def test_monitor_unresolved_stopped_case_preserves_history_and_research(override_db_session):
    db=override_db_session; case=ResearchCaseService(db).create_case('signal_first')
    case.status='stopped'; db.commit(); budget=dict(case.research_budget)
    first=save(db,case)
    later=save(db,case,plan(expected_prior_id=first['id'],due_on='2026-10-01',reason='Delay the manual review until new business evidence is available.'))
    assert later['prior_id']==first['id']
    assert db.get(CaseMonitoring,first['id']).content['due_on']=='2026-09-15'
    assert case.status=='stopped' and case.research_budget==budget
    assert service.queue(db,'reviewer',as_of=date(2026,9,15))['due_count']==0
    assert service.queue(db,'reviewer',scope='active')['items'][0]['id']==later['id']
    assert db.scalar(select(func.count(AuditEvent.id)).where(AuditEvent.action=='case_monitoring_recorded'))==2


def test_personal_chain_replay_and_stale_write(override_db_session):
    db=override_db_session; case=ResearchCaseService(db).create_case('hybrid');key=uuid4();p=plan()
    first=save(db,case,p,key)
    save(db,case,plan(expected_prior_id=first['id'],state='paused'))
    assert save(db,case,p,key)['id']==first['id']
    with pytest.raises(ValueError,match='Monitoring changed'):save(db,case,p)
    db.rollback()
    with pytest.raises(ValueError,match='another monitoring'):save(db,case,p,key,owner='other')
    db.rollback()
    other=save(db,case,owner='other')
    assert other['prior_id'] is None
    assert service.queue(db,'reviewer',as_of=date(2026,9,15))['items']==[]
    assert service.queue(db,'other',as_of=date(2026,9,15))['due_count']==1


def test_utc_due_boundary_filters_and_pagination(override_db_session):
    db=override_db_session
    for _ in range(11):save(db,ResearchCaseService(db).create_case('hybrid'),owner='pagination')
    day=date(2026,9,15)
    assert service.queue(db,'pagination',as_of=date(2026,9,14))['due_count']==0
    result=service.queue(db,'pagination',as_of=day)
    assert len(result['items'])==10 and result['has_next'] and result['due_count']==11
    assert len(service.queue(db,'pagination',as_of=day,page=2)['items'])==1
    assert not service.queue(db,'pagination',scope='paused')['items']
    assert not service.queue(db,'stranger',scope='all')['items']
    with pytest.raises(ValueError):plan(due_on='2026-02-30')
    with pytest.raises(ValueError):plan(question=' '*10)


def test_api_permissions_personal_history_and_reopen(client,override_db_session):
    from app.main import app
    from app.auth.service import Identity,current_identity
    db=override_db_session;case=ResearchCaseService(db).create_case('hybrid');role='viewer';subject='a'
    app.dependency_overrides[current_identity]=lambda:Identity(None,'demo',subject,None,'Named Reviewer',role=role)
    url=f'/api/monitoring/cases/{case.id}';body={'request_key':str(uuid4()),'monitoring':plan().model_dump()}
    try:
        assert client.post(url,json=body).status_code==403
        role='analyst';r=client.post(url,json=body);assert r.status_code==200
        first=r.json();assert first['actor']=='Named Reviewer'
        assert client.get(url).json()['latest']['id']==first['id']
        subject='b';assert client.get(url).json()['items']==[]
        assert client.get('/api/monitoring/cases?scope=all').json()['items']==[]
        assert client.post(url,json=body).status_code==409
        assert client.get('/api/monitoring/cases?scope=invalid').status_code==422
        assert client.get(url+'?page=0').status_code==422
        assert client.get('/api/monitoring/cases/999999').status_code==404
    finally:app.dependency_overrides.pop(current_identity,None)


def test_migration_reopen_preserves_monitoring(tmp_path):
    from alembic import command
    from app.ops.schema import alembic_config
    url='sqlite:///'+(tmp_path/'monitoring.db').as_posix();cfg=alembic_config(url)
    command.upgrade(cfg,'b174a0b1d837');command.upgrade(cfg,'head');engine=create_engine(url)
    with Session(engine) as db:
        case=ResearchCaseService(db).create_case('hybrid');r=save(db,case)
    with Session(engine) as db:
        assert service.view(db.get(CaseMonitoring,r['id']))==r
    with pytest.raises(RuntimeError,match='Cannot discard retained case monitoring'):
        command.downgrade(cfg,'b174a0b1d837')
