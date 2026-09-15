from uuid import uuid4
import pytest
from sqlalchemy import select,func,create_engine
from sqlalchemy.orm import Session
from app.domain.models import CaseDecision,CaseBriefVersion,AuditEvent
from app.research.cases import ResearchCaseService
from app.research import case_decisions as service,brief_versions


def setup(db):
    case=ResearchCaseService(db).create_case('hybrid')
    e=ResearchCaseService(db).add_evidence(case.id,source_mode='case_specific_research',canonical_url='https://example.test/fictional-decision',publisher='Fictional Source',source_type='other',content=str(uuid4()).encode(),relevant_excerpt='An uncertain fictional business clue.',extracted_facts={},provenance={})
    p=brief_versions.preview(db,case.id)
    b=brief_versions.save(db,case.id,request_key=uuid4(),expected_hash=p['content_hash'],expected_version=0,actor='Reviewer',actor_key='reviewer')
    return case,e,b


def payload(**kw):
    return service.DecisionInput(**{'brief_version':1,'expected_prior_id':None,'outcome':'more_research','purpose':'acquisition_exploration','rationale':'Business identity and ownership remain unknown.','next_action':'Find an independent source for business identity.',**kw})
def save(db,case,p=None,key=None,actor_key='reviewer'):
    return service.save(db,case.id,p or payload(),request_key=key or uuid4(),actor='Reviewer',actor_key=actor_key)


def test_decisions_preserve_research_and_immutable_brief(override_db_session):
    db=override_db_session;case,e,b=setup(db);before=dict(case.research_budget)
    case.status='stopped';db.commit()
    r=save(db,case,payload(supporting_source_ids=[e.id]))
    assert r['decision']['outcome']=='more_research' and r['brief_id']==b['id']
    assert db.get(type(case),case.id).status=='stopped' and case.research_budget==before
    assert db.get(CaseBriefVersion,b['id']).content==b['content']
    assert db.scalar(select(AuditEvent).where(AuditEvent.action=='case_decision_recorded')).actor=='Reviewer'


def test_correction_chain_duplicate_recovery_and_stale_rejection(override_db_session):
    db=override_db_session;case,e,b=setup(db);key=uuid4();p=payload()
    first=save(db,case,p,key)
    second=save(db,case,payload(expected_prior_id=first['id'],outcome='dismiss',change_reason='Further review found the clue irrelevant to this purpose.'))
    assert second['prior_id']==first['id'] and save(db,case,p,key)==first
    assert db.get(CaseDecision,first['id']).content['outcome']=='more_research'
    with pytest.raises(ValueError,match='Decision changed'): save(db,case,p)
    db.rollback()
    with pytest.raises(ValueError,match='another decision'): save(db,case,p,key,actor_key='other')
    db.rollback()
    with pytest.raises(ValueError,match='requires a reason'): payload(expected_prior_id=second['id'])


def test_sources_must_exist_in_exact_saved_case_version(override_db_session):
    db=override_db_session;case,e,b=setup(db);other,foreign,_=setup(db)
    with pytest.raises(ValueError,match='saved brief version'): save(db,case,payload(supporting_source_ids=[foreign.id]))
    db.rollback()
    with pytest.raises(ValueError,match='not found'): save(db,case,payload(brief_version=2))
    db.rollback()
    with pytest.raises(ValueError,match='supporting or contradicting'): payload(supporting_source_ids=[e.id],contradicting_source_ids=[e.id])
    with pytest.raises(ValueError,match='repeat'): payload(supporting_source_ids=[e.id,e.id])
    assert db.scalar(select(func.count(CaseDecision.id)).where(CaseDecision.case_id==case.id))==0


def test_api_permissions_history_and_next_action_persistence(client,override_db_session):
    from app.main import app
    from app.auth.service import Identity,current_identity
    db=override_db_session;case,e,b=setup(db);role='viewer'
    app.dependency_overrides[current_identity]=lambda:Identity(None,'demo','test',None,'Named Reviewer',role=role)
    url=f'/api/research/cases/{case.id}/decisions';body={'request_key':str(uuid4()),'decision':payload().model_dump()}
    try:
        assert client.post(url,json=body).status_code==403
        role='analyst';r=client.post(url,json=body);assert r.status_code==200
        first=r.json();assert first['actor']=='Named Reviewer'
        assert client.post(url,json=body).json()==first
        prior=first['id']
        for _ in range(10):
            r=save(db,case,payload(expected_prior_id=prior,change_reason='Additional review confirmed the next research action.'));prior=r['id']
        history=client.get(url).json();assert len(history['items'])==10 and history['has_next'] and history['latest']['id']==prior
        assert len(client.get(url+'?page=2').json()['items'])==1
        assert client.get(url+'?page=0').status_code==422
    finally: app.dependency_overrides.pop(current_identity,None)


def test_migration_reopen_and_downgrade_guard(tmp_path):
    from alembic import command
    from app.ops.schema import alembic_config
    url='sqlite:///'+(tmp_path/'decisions.db').as_posix();cfg=alembic_config(url)
    command.upgrade(cfg,'a172a0b1d836');command.upgrade(cfg,'head');engine=create_engine(url)
    with Session(engine) as db:
        case,e,b=setup(db);r=save(db,case)
    with Session(engine) as db:
        assert service.view(db.get(CaseDecision,r['id']))==r
    with pytest.raises(RuntimeError,match='Cannot discard retained case decisions'): command.downgrade(cfg,'a172a0b1d836')
