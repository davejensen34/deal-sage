import asyncio
from datetime import datetime,timedelta,timezone
from uuid import uuid4
import pytest
from sqlalchemy import select,func,create_engine
from sqlalchemy.orm import Session
from app.core.config import Settings,get_settings
from app.domain.models import (FollowupRun,FollowupAttempt,ResearchFrontierItem,ResearchStep,SourceCandidate)
from app.research import followups
from app.research.cases import ResearchCaseService
from app.research.discovery_runs import execute_attempt,recover
from app.research.search import FixtureSearchProvider


def settings(): return Settings(_env_file=None,demo_mode=True,auth_mode='demo',web_search_provider='disabled')
def config(): return followups.FollowupSettings(question='Does the fictional business still operate?',rationale='Operating status is unknown from current evidence.',query='Fictional Acme operating status')
def make(db,case=None):
    case=case or ResearchCaseService(db).create_case('hybrid',{'max_queries':0})
    p=followups.preview(db,case.id,config(),settings())
    return case,followups.create(db,case.id,config(),settings(),request_key=uuid4(),expected_hash=p['hash'],actor='Reviewer',actor_key='reviewer')
def execute(db,run,**kw):
    return asyncio.run(execute_attempt(db,run,settings(),request_key=kw.pop('key',uuid4()),expected_revision=run.revision,actor='Operator',**kw))


def test_followup_search_preserves_budget_and_never_answers_question(override_db_session):
    db=override_db_session;case,run=make(db);budget=dict(case.research_budget);key=uuid4()
    result=execute(db,run,key=key)
    assert result['status']=='completed' and result['record_count']==1
    assert execute(db,run,key=key)==result
    assert db.get(ResearchFrontierItem,run.frontier_id).status=='pending'
    assert db.scalar(select(func.count(FollowupAttempt.id)))==1
    assert db.get(type(case),case.id).research_budget==budget
    step=db.scalar(select(ResearchStep).where(ResearchStep.frontier_item_id==run.frontier_id))
    assert step.status=='succeeded' and step.result_summary['question_resolved'] is False
    with pytest.raises(ValueError,match='No planned'): execute(db,run)


def test_failed_retry_empty_result_and_exhaustion(override_db_session):
    db=override_db_session;case,run=make(db)
    result=execute(db,run,provider=FixtureSearchProvider(error=RuntimeError('private body')))
    assert result['attempts'][0]['error_code']=='search_failed'
    result=execute(db,run,retry_last=True,provider=FixtureSearchProvider())
    assert [a['status'] for a in result['attempts']]==['failed','succeeded']
    assert result['attempts'][1]['result_count']==0
    assert db.get(ResearchFrontierItem,run.frontier_id).status=='blocked'
    with pytest.raises(ValueError,match='exhausted'): execute(db,run,retry_last=True)


def test_stale_creation_identity_and_plan_ceiling(override_db_session):
    db=override_db_session;case,run=make(db)
    kw=dict(request_key=run.request_key,expected_hash=run.plan_hash,actor='Reviewer',actor_key='reviewer')
    assert followups.create(db,case.id,config(),settings(),**kw).id==run.id
    with pytest.raises(ValueError,match='another'): followups.create(db,case.id,config(),settings(),**{**kw,'actor_key':'other'})
    db.rollback()
    with pytest.raises(ValueError,match='changed'): followups.create(db,case.id,config(),settings(),**{**kw,'request_key':uuid4(),'expected_hash':'0'*64})
    db.rollback()
    for _ in range(9): make(db,case)
    with pytest.raises(ValueError,match='ten follow-up'): make(db,case)
    db.rollback();case.status='stopped';db.commit()
    with pytest.raises(ValueError,match='stopped'): execute(db,run)


def test_recovery_fences_late_results_and_keeps_question_unresolved(override_db_session):
    db=override_db_session;case,run=make(db)
    class Delayed(FixtureSearchProvider):
        async def search(self,query,max_results):
            attempt=db.scalar(select(FollowupAttempt).where(FollowupAttempt.run_id==run.id))
            attempt.recovery_after=datetime.now(timezone.utc)-timedelta(seconds=1);db.commit()
            recover(db,run,expected_revision=run.revision,actor='Recovery reviewer')
            from app.research.search import SearchResult
            return [SearchResult(url='https://example.test/late',title='Late',publisher='Fixture',relevance_reason='Late clue',proposed_use='case_specific_research')]
    result=execute(db,run,provider=Delayed())
    assert result['attempts'][0]['status']=='unknown'
    assert result['record_count']==0
    assert db.get(ResearchFrontierItem,run.frontier_id).status=='pending'
    assert db.scalar(select(ResearchStep).where(ResearchStep.frontier_item_id==run.frontier_id)).status=='unknown'


def test_api_permissions_and_persisted_history(client,override_db_session):
    from app.auth.service import current_identity,Identity
    from app.main import app
    db=override_db_session;case=ResearchCaseService(db).create_case('signal_first');role='viewer'
    app.dependency_overrides[current_identity]=lambda:Identity(None,'demo','test',None,'Reviewer',role=role)
    app.dependency_overrides[get_settings]=settings
    try:
        base=f'/api/followups/cases/{case.id}'
        assert client.post(base+'/preview',json=config().model_dump()).status_code==403
        role='analyst';p=client.post(base+'/preview',json=config().model_dump()).json()
        payload={'settings':config().model_dump(),'request_key':str(uuid4()),'expected_hash':p['hash']}
        r=client.post(base,json=payload);assert r.status_code==200
        run=r.json();assert client.post(base,json=payload).json()['id']==run['id']
        url=f"/api/followups/runs/{run['id']}/execute";attempt={'request_key':str(uuid4()),'expected_revision':0}
        assert client.post(url,json=attempt).status_code==403
        role='operator';assert client.post(url,json=attempt).status_code==200
        assert client.get(base).json()['items'][0]['actor']=='Reviewer'
        assert client.get('/api/followups/runs/999999').status_code==404
    finally:
        app.dependency_overrides.pop(current_identity,None);app.dependency_overrides.pop(get_settings,None)


def test_migration_and_reopen_retained_followup(tmp_path):
    from app.ops.schema import alembic_config
    from alembic import command
    url='sqlite:///'+(tmp_path/'followups.db').as_posix();cfg=alembic_config(url)
    command.upgrade(cfg,'f170a0b1d835');command.upgrade(cfg,'head');engine=create_engine(url)
    with Session(engine) as db:
        case,run=make(db);execute(db,run);run_id=run.id
    with Session(engine) as db:
        assert db.get(FollowupRun,run_id).status=='completed'
    with pytest.raises(RuntimeError,match='Cannot discard retained follow-up'): command.downgrade(cfg,'f170a0b1d835')


def test_other_session_cannot_execute_a_second_followup_while_first_runs(override_db_session):
    db=override_db_session;case,first=make(db);_,second=make(db,case)
    class CheckConcurrent(FixtureSearchProvider):
        async def search(self,query,max_results):
            with Session(db.get_bind()) as other:
                run=other.get(FollowupRun,second.id)
                with pytest.raises(ValueError,match='Another follow-up'):
                    await execute_attempt(other,run,settings(),request_key=uuid4(),expected_revision=0,actor='Other')
                other.rollback()
            return []
    assert execute(db,first,provider=CheckConcurrent())['status']=='completed'
    assert db.scalar(select(func.count(FollowupAttempt.id)).where(FollowupAttempt.run_id==second.id))==0


def test_provider_drift_blocks_before_reservation(override_db_session):
    db=override_db_session;case,run=make(db)
    disabled=Settings(_env_file=None,demo_mode=False,auth_mode='demo',web_search_provider='disabled')
    with pytest.raises(ValueError,match='configuration'):
        asyncio.run(execute_attempt(db,run,disabled,request_key=uuid4(),expected_revision=0,actor='Operator'))
    db.rollback()
    assert db.scalar(select(func.count(FollowupAttempt.id)).where(FollowupAttempt.run_id==run.id))==0
