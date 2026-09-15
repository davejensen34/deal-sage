from uuid import uuid4
import pytest
from app.research.case_decisions import ReviewFeedback
from app.services.case_workflow_metrics import case_workflow_metrics
from app.domain.models import DiscoveryRun, DiscoveryAttempt, CaseDecision
from app.domain.models import now
from test_case_decisions import setup, payload, save


@pytest.fixture
def override_db_session():
    # Workspace denominators need a genuinely empty database, independent of
    # the shared legacy test corpus and decisions made by earlier tests.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool
    from app.core.database import Base, get_db
    from app.main import app
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    original=app.dependency_overrides[get_db]
    with Session(engine,expire_on_commit=False) as db:
        app.dependency_overrides[get_db]=lambda:db
        try:yield db
        finally:app.dependency_overrides[get_db]=original
    engine.dispose()


def test_feedback_validation():
    for data in ({'usefulness':'useful','reason':'   '},
                 {'usefulness':'not_useful','reason':'Too short'},
                 {'usefulness':'not_assessed','review_seconds':0},
                 {'usefulness':'not_assessed','review_seconds':86401},
                 {'usefulness':'not_assessed','review_seconds':True},
                 {'usefulness':'not_assessed','review_seconds':1.5}):
        with pytest.raises(ValueError): ReviewFeedback(**data)
    assert ReviewFeedback(usefulness='not_assessed').review_seconds is None


def test_latest_denominators_times_corrections_and_legacy_replay(override_db_session):
    db=override_db_session
    a,_,_=setup(db);b,_,_=setup(db);c,_,_=setup(db);setup(db)
    key=uuid4();old=save(db,a,key=key)
    assert 'feedback' not in old['decision']
    new=save(db,a,payload(expected_prior_id=old['id'],change_reason='Updated with an explicit usefulness assessment.',
        feedback={'usefulness':'not_useful','reason':'The evidence does not meet the purpose.','review_seconds':120}))
    save(db,b,payload(feedback={'usefulness':'useful','reason':'Useful for a concrete follow-up question.','review_seconds':240}))
    save(db,c)
    assert save(db,a,key=key)==old
    assert db.get(CaseDecision,old['id']).content==old['decision']
    result=case_workflow_metrics(db)
    assert (result['total_cases'],result['cases_with_decisions'],result['cases_without_decisions'])==(4,3,1)
    p=result['purposes'][0]
    assert (p['assessed'],p['useful'],p['not_useful'],p['missing_judgments'])==(2,1,1,1)
    assert p['useful_percent']==50 and p['median_review_seconds']==180 and p['timed_reviews']==2
    assert result['purposes'][1]['useful_percent'] is None
    assert result['purposes'][1]['median_review_seconds'] is None
    assert len(result['items'])==3 and new['id'] in [r['id'] for r in result['items']]


def test_empty_pagination_and_failed_reservation_scope(client,override_db_session):
    db=override_db_session
    empty=case_workflow_metrics(db)
    assert empty['total_cases']==0 and empty['cases_without_decisions']==0
    for _ in range(11):
        case,_,_=setup(db);save(db,case)
    run=DiscoveryRun(case_id=case.id,request_key=str(uuid4()),plan={},plan_hash='f'*64,actor='QA',reserved_cents=24)
    db.add(run);db.flush()
    for status in ('failed','interrupted'):
        db.add(DiscoveryAttempt(run_id=run.id,request_key=str(uuid4()),slot=0,actor='QA',status=status,reserved_cents=12,recovery_after=now()))
    db.commit()
    result=client.get('/api/research/case-workflow-measures').json()
    assert len(result['items'])==10 and result['has_next']
    assert len(client.get('/api/research/case-workflow-measures?page=2').json()['items'])==1
    assert client.get('/api/research/case-workflow-measures?page=0').status_code==422
    assert result['reservations'][0]=={'kind':'discovery','attempts':2,'reserved_cents':24,'outcomes':{'failed':1,'interrupted':1}}
    assert 'Actual spend is not measured' in result['cost_scope']


def test_feedback_api_permissions_and_retry(client,override_db_session):
    from app.main import app
    from app.auth.service import Identity,current_identity
    db=override_db_session;case,_,_=setup(db);role='viewer'
    app.dependency_overrides[current_identity]=lambda:Identity(None,'demo','test',None,'Named Reviewer',role=role)
    body={'request_key':str(uuid4()),'decision':payload(feedback={'usefulness':'not_useful','reason':'Missing evidence for this review purpose.'}).model_dump()}
    url=f'/api/research/cases/{case.id}/decisions'
    try:
        assert client.get('/api/research/case-workflow-measures').status_code==200
        assert client.post(url,json=body).status_code==403
        role='analyst';r=client.post(url,json=body);assert r.status_code==200
        assert r.json()['decision']['feedback']['usefulness']=='not_useful'
        assert client.post(url,json=body).json()==r.json()
    finally:app.dependency_overrides.pop(current_identity,None)
