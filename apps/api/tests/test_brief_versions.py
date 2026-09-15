from uuid import uuid4
import asyncio
import pytest
from sqlalchemy import select,func,create_engine
from sqlalchemy.orm import Session
from app.core.config import Settings
from app.domain.models import CaseBriefVersion, CaseEvidence, AuditEvent, ModelProposalDisposition, ExtractionAttempt, ModelProposal
from app.research.cases import ResearchCaseService
from app.research import brief_versions as service, extraction_attempts
from app.auth.service import Identity,current_identity
from app.main import app


def setup(db):
    case=ResearchCaseService(db).create_case('signal_first')
    evidence=ResearchCaseService(db).add_evidence(case.id,source_mode='case_specific_research',canonical_url='https://example.test/fictional-discovery/brief',publisher='Fictional source',source_type='other',content=str(uuid4()).encode(),relevant_excerpt=extraction_attempts.FIXTURE_EXCERPT,extracted_facts={'business_name':'Fictional Acme'},provenance={'private_marker':'not in brief'})
    return case,evidence


def save(db,case,prepared=None,**kwargs):
    p=prepared or service.preview(db,case.id)
    return service.save(db,case.id,request_key=kwargs.pop('key',uuid4()),expected_hash=p['content_hash'],expected_version=p['latest_version'],actor='Reviewer',actor_key=kwargs.pop('actor_key','reviewer'),**kwargs)


def test_versions_keep_sources_immutable_and_report_changes(override_db_session):
    db=override_db_session;case,evidence=setup(db)
    p=service.preview(db,case.id)
    assert db.scalar(select(func.count(CaseBriefVersion.id)).where(CaseBriefVersion.case_id==case.id))==0
    assert 'private_marker' not in str(p)
    first=save(db,case,p)
    assert first['version']==1 and first['content']['source_brief']['title']=='Fictional Acme'
    assert service.preview(db,case.id)['unchanged']
    evidence.extracted_facts={'business_name':'Fictional Acme','revenue':'Source-reported USD 2 million in 2024'}
    evidence.relevant_excerpt='New fictional source text';db.commit()
    p=service.preview(db,case.id)
    assert not p['unchanged'] and p['changes']['sources']['changed']==[evidence.id]
    second=save(db,case,p)
    assert second['version']==2
    retained=db.get(CaseBriefVersion,first['id'])
    assert retained.content['sources'][0]['relevant_excerpt']==extraction_attempts.FIXTURE_EXCERPT
    assert retained.content['source_brief']['facts']!=second['content']['source_brief']['facts']


def test_stale_previews_versions_and_duplicate_keys(override_db_session):
    db=override_db_session;case,evidence=setup(db);p=service.preview(db,case.id);key=uuid4()
    first=save(db,case,p,key=key)
    assert save(db,case,p,key=key)==first
    with pytest.raises(ValueError,match='changed'): save(db,case,p)
    with pytest.raises(ValueError,match='No included'): save(db,case)
    evidence.relevant_excerpt='Changed after the saved version';db.commit()
    assert save(db,case,p,key=key)==first
    with pytest.raises(ValueError,match='another brief'): save(db,case,p,key=key,actor_key='another-reviewer')
    assert db.scalar(select(func.count(CaseBriefVersion.id)).where(CaseBriefVersion.case_id==case.id))==1


def test_rejected_model_observations_remain_separate_from_source_facts(override_db_session):
    db=override_db_session;case,evidence=setup(db)
    cfg=Settings(_env_file=None,demo_mode=True,auth_mode='demo')
    p=extraction_attempts.preview(db,case.id,evidence.id,cfg)
    result=asyncio.run(extraction_attempts.execute(db,case.id,evidence.id,cfg,request_key=uuid4(),expected_hash=p['plan_hash'],actor='Operator',actor_key='operator'))
    proposal_id=result['proposal']['id']
    first=save(db,case)
    assert first['content']['model_observations'][0]['review_state']=='unreviewed'
    db.add(ModelProposalDisposition(case_id=case.id,proposal_id=proposal_id,analyst_name='Human',decision='reject',rationale='Wrong business context',supporting_evidence_ids=[evidence.id],supporting_claim_ids=[]));db.commit()
    current=service.preview(db,case.id)
    assert current['content']['model_observations'][0]['review_state']=='reject'
    assert current['changes']['reviews']['added']
    assert current['content']['source_brief']==first['content']['source_brief']
    second=save(db,case,current)
    assert second['content']['reviews'][0]['rationale']=='Wrong business context'
    assert db.get(CaseBriefVersion,first['id']).content['reviews']==[]


def test_empty_case_and_size_boundaries_do_not_fabricate_or_partially_save(override_db_session):
    db=override_db_session;case=ResearchCaseService(db).create_case('hybrid')
    result=save(db,case)
    assert result['content']['source_brief']['title']=='Business not yet identified'
    assert result['content']['sources']==[] and result['content']['model_scope']['included']==0
    other,evidence=setup(db)
    evidence.extracted_facts={'business_name':'x'*256001};db.commit()
    with pytest.raises(ValueError,match='snapshot ceiling'): save(db,other)
    assert db.scalar(select(func.count(CaseBriefVersion.id)).where(CaseBriefVersion.case_id==other.id))==0


def test_api_permissions_case_scope_pagination_and_record_attribution(client,override_db_session):
    db=override_db_session;case,evidence=setup(db);other,_=setup(db);role='viewer'
    app.dependency_overrides[current_identity]=lambda:Identity(None,'demo','test',None,'Human reviewer',role=role)
    base=f'/api/research/cases/{case.id}'
    try:
        p=client.get(base+'/brief-preview').json()
        payload={'request_key':str(uuid4()),'expected_hash':p['content_hash'],'expected_version':0}
        assert client.post(base+'/brief-versions',json=payload).status_code==403
        role='analyst'
        result=client.post(base+'/brief-versions',json=payload)
        assert result.status_code==200 and result.json()['actor']=='Human reviewer'
        assert client.get(f'/api/research/cases/{other.id}/brief-versions/1').status_code==404
        for n in range(10):
            evidence.relevant_excerpt=f'Fictional revision {n}';db.commit();save(db,case)
        page=client.get(base+'/brief-versions').json()
        assert len(page['items'])==10 and page['has_next']
        assert 'content' not in page['items'][0]
        tail=client.get(base+'/brief-versions?page=2').json()
        assert len(tail['items'])==1 and not tail['has_next']
        assert client.get(base+'/brief-versions?page=0').status_code==422
        audits=db.scalars(select(AuditEvent).where(AuditEvent.action=='case_brief_saved')).all()
        assert any(a.actor=='Human reviewer' and a.after_state['case_id']==case.id for a in audits)
    finally: app.dependency_overrides.pop(current_identity,None)


def test_migration_reopen_and_retained_downgrade_guard(tmp_path):
    from app.ops.schema import alembic_config
    from alembic import command
    cfg=alembic_config('sqlite:///'+(tmp_path/'brief.db').as_posix())
    command.upgrade(cfg,'e168a0b1d834');command.upgrade(cfg,'head')
    engine=create_engine('sqlite:///'+(tmp_path/'brief.db').as_posix())
    with Session(engine) as db:
        case,evidence=setup(db);saved=save(db,case)
    with Session(engine) as db:
        assert service.view(db.get(CaseBriefVersion,saved['id']))==saved
    with pytest.raises(RuntimeError,match='Cannot discard retained case brief'):
        command.downgrade(cfg,'e168a0b1d834')
