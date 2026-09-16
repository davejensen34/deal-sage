from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import select, func

from app.domain.models import ClaimContradiction, EvidenceClaim, ResearchInference
from app.research.cases import ResearchCaseService
from app.research.target_fit import TargetProfile, assess_target_fit

TODAY=date(2026,9,16)


def profile(**kw):
    return TargetProfile(purpose=kw.pop('purpose','acquisition_exploration'),**kw)


def case(db):
    return ResearchCaseService(db).create_case('signal_first',{'max_model_calls':0})


def claim(db,c,predicate='company_type',value='private',unit='category',**overrides):
    service=ResearchCaseService(db)
    text=f'Fictional Acme reports {predicate}: {value} ({unit}).'
    evidence=service.add_evidence(c.id,source_mode='case_specific_research',
        canonical_url='https://example.test/'+str(uuid4()),publisher='Fictional Acme',source_type='business_website',
        content=text.encode(),relevant_excerpt=text,extracted_facts={},provenance={})
    payload={'version':'target-fact-v1','business_key':'acme-id','value':value,'unit':unit,
        'observed_on':'2026-09-01','quote':text,**overrides}
    return service.add_claim(c.id,evidence.id,subject_type='business',predicate=predicate,
        object_value=payload,confidence=.8,classification='source_fact',source_authority='self_published',directness='direct_statement')


def assess(db,c,p=None):
    return assess_target_fit(db,c.id,'acme-id',p or profile(),assessment_date=TODAY)


def test_purpose_defaults_do_not_invent_size_or_apply_acquisition_to_marketing():
    assert profile().effective_company_types().values==['private']
    assert profile().employees is None and profile().annual_revenue_usd is None
    for purpose in ['marketing_introduction','succession_advisory']:
        assert profile(purpose=purpose).effective_company_types() is None


@pytest.mark.parametrize('kw',[
    {'employees':{'minimum':100,'maximum':10}},
    {'employees':{}}, {'employees':{'minimum':True}},
    {'annual_revenue_usd':{'minimum':'1000'}},
    {'company_types':{'values':['executive']}},
    {'industries':{'values':['Manufacturing']}},
    {'industries':{'values':['manufacturing','manufacturing']}},
    {'industries':{'values':['manufacturing']},'excluded_industries':['manufacturing']},
    {'max_fact_age_days':0}, {'unknown_setting':'ignored'},
])
def test_invalid_profiles_fail_closed(kw):
    with pytest.raises(ValidationError):profile(**kw)


def test_required_unknown_is_not_mismatch_and_optional_unknown_does_not_block(override_db_session):
    db=override_db_session;c=case(db)
    assert assess(db,c)['status']=='unresolved'
    row=claim(db,c)
    result=assess(db,c,profile(employees={'minimum':10,'required':False}))
    assert result['status']=='requirements_met' and result['readiness']=='not_assessed'
    company=result['factors'][0]
    assert company['observations'][0]['claim_id']==row.id
    assert company['observations'][0]['evidence_id']==row.evidence_id
    assert company['observations'][0]['content_hash']
    assert result['factors'][2]['state']=='unknown'
    assert assess(db,c,profile(employees={'minimum':10,'required':True}))['status']=='unresolved'


def test_public_company_mismatch_is_purpose_specific(override_db_session):
    db=override_db_session;c=case(db);claim(db,c,value='public')
    assert assess(db,c)['status']=='not_fit'
    marketing=assess(db,c,profile(purpose='marketing_introduction'))
    assert marketing['status']=='no_required_factors' and marketing['readiness']=='not_assessed'
    preferred=assess(db,c,profile(company_types={'values':['private'],'required':False}))
    assert preferred['status']=='no_required_factors'
    assert preferred['factors'][0]['state']=='mismatch'


def test_conflicts_cannot_be_resolved_by_majority_or_matching_values(override_db_session):
    db=override_db_session;c=case(db);a=claim(db,c);b=claim(db,c,value='public');claim(db,c)
    assert assess(db,c)['factors'][0]['state']=='conflicting'
    b.status='retracted';db.commit()
    assert assess(db,c)['status']=='requirements_met'
    db.add(ClaimContradiction(case_id=c.id,left_claim_id=a.id,right_claim_id=b.id,
        contradiction_type='identity',rationale='Same name may refer to another business',status='open'))
    db.commit()
    assert assess(db,c)['status']=='unresolved'


@pytest.mark.parametrize('changes,reason',[
    ({'business_key':'another-business'},'different_business'),
    ({'quote':'A quote absent from the retained source'},'citation_not_grounded'),
    ({'observed_on':'2020-01-01'},'outside_fact_window'),
    ({'observed_on':'2027-01-01'},'outside_fact_window'),
    ({'unit':'employees','value':50},'wrong_semantics_or_unit'),
    ({'value':'registered_agent'},'wrong_semantics_or_unit'),
    ({'score':100},'untyped_or_invalid_fact'),
])
def test_ineligible_claims_remain_visible_without_entering_fit(override_db_session,changes,reason):
    db=override_db_session;c=case(db);row=claim(db,c,**changes)
    result=assess(db,c)
    assert result['status']=='unresolved'
    assert {'claim_id':row.id,'reason':reason} in result['ignored_claims']


def test_case_isolation_subject_inference_and_provenance_guards(override_db_session):
    db=override_db_session;c=case(db);other=case(db);claim(db,other)
    assert assess(db,c)['status']=='unresolved'
    row=claim(db,c);row.classification='dealsage_inference';db.commit()
    assert assess(db,c)['status']=='unresolved'
    row.classification='source_fact';row.subject_type='person';db.commit()
    assert assess(db,c)['status']=='unresolved'
    row.subject_type='business';row.evidence_id=claim(db,other).evidence_id;db.commit()
    assert assess(db,c)['status']=='unresolved'
    assert assess(db,c)['ignored_claims'][0]['reason']=='citation_not_grounded'


def test_size_units_reporting_period_and_exclusions(override_db_session):
    db=override_db_session;c=case(db);claim(db,c)
    size=claim(db,c,'employee_count',50,'employees')
    p=profile(employees={'minimum':10,'maximum':50,'required':True})
    assert assess(db,c,p)['status']=='requirements_met'
    size.object_value={**size.object_value,'value':'50 branches'};db.commit()
    assert assess(db,c,p)['status']=='unresolved'
    revenue=claim(db,c,'annual_revenue',1000000,'USD/year',period_start='2025-01-01',period_end='2025-12-31')
    p=profile(annual_revenue_usd={'minimum':500000,'required':True})
    assert assess(db,c,p)['status']=='requirements_met'
    revenue.object_value={**revenue.object_value,'period_start':'2025-10-01'};db.commit()
    assert assess(db,c,p)['status']=='unresolved'
    revenue.object_value={**revenue.object_value,'period_start':'2020-01-01','period_end':'2020-12-31'};db.commit()
    assert assess(db,c,p)['status']=='unresolved'
    claim(db,c,'industry','manufacturing')
    excluded=profile(excluded_industries=['manufacturing'])
    assert assess(db,c,excluded)['status']=='not_fit'


def test_assessment_is_repeatable_read_only_and_hash_tracks_input(override_db_session):
    db=override_db_session;c=case(db);row=claim(db,c)
    counts=[db.scalar(select(func.count(m.id))) for m in (EvidenceClaim,ResearchInference)]
    first=assess(db,c)
    assert first==assess(db,c)
    assert counts==[db.scalar(select(func.count(m.id))) for m in (EvidenceClaim,ResearchInference)]
    row.object_value={**row.object_value,'value':'public'};db.commit()
    assert first['content_hash']!=assess(db,c)['content_hash']
