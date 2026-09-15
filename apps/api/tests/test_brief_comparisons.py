from copy import deepcopy

import pytest
from sqlalchemy import select, func

from app.domain.models import AuditEvent, CaseBriefVersion
from app.research import brief_comparisons as service
from test_brief_versions import setup, save


def test_compare_exposes_add_change_remove_and_context_without_judgment():
    before={g:[] for g in service.GROUPS}
    before.update(case_status='open',source_brief={'timing':None},transitions=[])
    before['sources']=[{'id':1,'relevant_excerpt':'Earlier quote','published_at':None},{'id':2,'relevant_excerpt':'Removed snapshot item'}]
    after=deepcopy(before)
    after['sources']=[{'id':1,'relevant_excerpt':'Later quote','published_at':'2026-09-15'},{'id':3,'relevant_excerpt':'New unverified report'}]
    after['source_brief']={'timing':{'route':'future'}}
    after['reviews']=[{'id':9,'decision':'reject','rationale':'Wrong identity'}]
    after['model_observations']=[{'id':8,'observations':[],'review_state':'reject'}]
    result=service.compare_content(before,after)
    assert result['groups']['sources']['counts']=={'added':1,'changed':1,'removed':1}
    rows=result['groups']['sources']['rows']
    assert rows[0]['fields']==['published_at','relevant_excerpt']
    assert rows[1]['after'] is None and rows[2]['before'] is None
    assert result['context_changes']==[{'field':'source_brief','before':{'timing':None},'after':{'timing':{'route':'future'}}}]
    assert result['groups']['reviews']['rows'][0]['after']['decision']=='reject'
    assert result['groups']['model_observations']['rows'][0]['after']['review_state']=='reject'
    assert service.compare_content(before,before)['unchanged']


def test_saved_comparison_is_immutable_and_read_only(override_db_session):
    db=override_db_session;case,e=setup(db);first=save(db,case)
    e.relevant_excerpt='Fictional changed source excerpt, ownership still unknown.';db.commit()
    second=save(db,case)
    audits=db.scalar(select(func.count(AuditEvent.id)));budget=dict(case.research_budget)
    initial=service.compare(db,case.id,1,2)
    e.relevant_excerpt='Later unsaved edits must not appear.';db.commit()
    assert service.compare(db,case.id,1,2)==initial
    assert initial['from']['content_hash']==first['content_hash'] and initial['to']['content_hash']==second['content_hash']
    assert initial['groups']['sources']['rows'][0]['before']['relevant_excerpt']==first['content']['sources'][0]['relevant_excerpt']
    assert db.scalar(select(func.count(AuditEvent.id)))==audits and case.research_budget==budget
    assert db.get(CaseBriefVersion,first['id']).content==first['content']
    assert service.compare(db,case.id,2,2)['unchanged']
    with pytest.raises(ValueError):service.compare(db,case.id,2,1)
    with pytest.raises(LookupError):service.compare(db,case.id,1,3)


def test_comparison_api_auth_scope_and_invalid_versions(client,override_db_session):
    from app.main import app
    from app.auth.service import current_identity,Identity
    from fastapi import HTTPException
    db=override_db_session;case,e=setup(db);save(db,case);other,_=setup(db)
    url=f'/api/research/cases/{case.id}/brief-comparison'
    app.dependency_overrides[current_identity]=lambda:Identity(None,'demo','reader',None,'Reader',role='viewer')
    try:
        assert client.get(url+'?from_version=1&to_version=1').json()['unchanged']
        assert client.get(url+'?from_version=0&to_version=1').status_code==422
        assert client.get(url+'?from_version=2&to_version=1').status_code==422
        assert client.get(url+'?from_version=1&to_version=2').status_code==404
        assert client.get(f'/api/research/cases/{other.id}/brief-comparison?from_version=1&to_version=1').status_code==404
        def deny():raise HTTPException(401,'Authentication required')
        app.dependency_overrides[current_identity]=deny
        assert client.get(url+'?from_version=1&to_version=1').status_code==401
    finally:app.dependency_overrides.pop(current_identity,None)
