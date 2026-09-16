import asyncio
from datetime import date

import pytest
from sqlalchemy import func, select

from app.ai.providers.base import TokenUsage
from app.auth.service import Identity, current_identity
from app.domain.models import AuditEvent, EvidenceClaim, ExtractionAttempt, ExtractionBatch, ModelProposal
from app.main import app
from app.research import extraction_attempts as extraction, observation_assessment as service
from app.research.target_fit import TargetProfile, SizeRange
from test_extraction_batches import setup, create, run


TODAY = date(2026, 9, 16)


@pytest.fixture(autouse=True)
def fixed_pricing(monkeypatch):
    original = extraction.policy
    monkeypatch.setattr(extraction, 'policy', lambda config: original(config, TODAY))


def observe(field, value, quote, **kwargs):
    return service.check({'field': field, 'value': value, 'quote': quote, 'certainty': 'source_reported'},
                         {'excerpt': kwargs.pop('excerpt', quote)}, TODAY)


@pytest.mark.parametrize('value,quote', [
    ('fourth', 'Acme is the fourth partner in the group.'),
    ('20', 'The bank operates 20 branches and has 300 employees.'),
    ('30', 'Jane has 30 years of experience and manages employees.'),
    ('42', 'Acme has about 42 employees.'),
    ('42', 'Acme has between 42 and 50 employees.'),
    ('42', 'Acme does not have 42 employees.'),
    ('42', 'Acme previously had 42 employees.'),
    ('42', 'Acme has 42-50 employees.'),
    ('42', 'Acme has 0.42 employees.'),
    ('42', 'Acme has 42 employees per branch.'),
])
def test_wrong_units_ranges_and_context_remain_clues(value, quote):
    result = observe('employee_count', value, quote)
    assert result['interpretation'] == 'needs_context' and result['normalized'] is None
    assert result['original']['quote'] == quote and not result['eligible_for_fit']


@pytest.mark.parametrize('value,quote,count', [
    ('42', 'Acme employs 42 people.', 42),
    ('1,200', 'Acme has 1,200 employees.', 1200),
    ('42', 'Acme employs 42 full-time employees.', 42),
])
def test_explicit_units_are_structured_clues_not_authoritative_facts(value, quote, count):
    result = observe('employee_count', value, quote)
    assert result['normalized'] == {'value': count, 'unit': 'employees'}
    assert not result['eligible_for_fit'] and 'business_subject_and_observation_date_unresolved' in result['reasons']


@pytest.mark.parametrize('value', ['NYSE:ACME', 'ACME', 'https://localhost/a', 'https://127.0.0.1/a',
                                  'https://user:pass@example.test/a', 'javascript:alert(1)'])
def test_tickers_and_nonpublic_urls_are_not_company_websites(value):
    result = observe('business_website', value, 'Website: ' + value)
    assert result['normalized'] is None and result['interpretation'] == 'needs_context'
    assert result['original']['value'] == value


def test_public_url_syntax_is_not_verified_business_affiliation():
    result = observe('business_website', 'https://example.test/about', 'See https://example.test/about')
    assert result['normalized'] == {'url': 'https://example.test/about'}
    assert result['reasons'] == ['url_syntax_only_business_affiliation_unverified']


@pytest.mark.parametrize('field,value,quote,reason', [
    ('event_date', '2026-09-01', 'Published 2026-09-01', 'announcement_or_publication_is_not_event_timing'),
    ('event_date', '2026-09-01', 'Announced September news on 2026-09-01', 'announcement_or_publication_is_not_event_timing'),
    ('event_date', '2027-01-01', 'The owner will retire on 2027-01-01.', 'planned_language_not_completed_event'),
    ('event_date', '2027-01-01', 'On 2027-01-01 the business changed.', 'future_date_not_a_completed_transition'),
    ('planned_event_date', '2027', 'Retirement planned for 2027.', 'exact_date_unresolved'),
])
def test_dates_do_not_silently_become_completed_transitions(field, value, quote, reason):
    result = observe(field, value, quote)
    assert reason in result['reasons'] and not result['eligible_for_fit']


def test_people_and_roles_do_not_establish_business_identity_or_ownership():
    result = observe('business_name', 'Jane Smith', 'Jane Smith, CEO of Acme Inc.')
    assert 'person_role_may_be_mislabeled_business' in result['reasons']
    assert result['original']['value'] == 'Jane Smith'
    for role in ['registered agent', 'CEO', 'founder', 'owner']:
        result = observe('reported_relationship', role, 'Jane is the ' + role)
        assert 'role_does_not_establish_ownership_or_sale_intent' in result['reasons']


def test_citation_and_financial_ambiguity_stay_visible():
    result = observe('industry', 'manufacturing', 'Acme does manufacturing.', excerpt='Different source')
    assert result['interpretation'] == 'citation_mismatch'
    result = observe('revenue', '$5 million', 'Acme earned $5 million.')
    assert result['normalized'] is None and result['original']['value'] == '$5 million'


def completed(db, tmp_path):
    case, _, _, _, settings, config, prepared = setup(db, tmp_path)
    batch = create(db, case, config, settings, prepared)
    async def provider(plan, settings):
        excerpt = plan['packet']['excerpt']
        observations = []
        if 'Fictional Acme employs 42 people.' in excerpt:
            observations = [{'field': 'employee_count', 'value': '42',
                'quote': 'Fictional Acme employs 42 people.', 'certainty': 'source_reported'}]
        return {'observations': observations, 'unresolved_questions': ['Who owns the business?']}, TokenUsage(100, 50, 150)
    run(db, case, batch, settings, provider)
    return case, batch


def test_assessment_is_read_only_reproducible_and_prioritizes_missing_identity(override_db_session, tmp_path):
    db = override_db_session; case, batch = completed(db, tmp_path)
    audit_count = db.scalar(select(func.count(AuditEvent.id)))
    result = service.assess(db, case.id, batch['id'], assessment_date=TODAY)
    assert result == service.assess(db, case.id, batch['id'], assessment_date=TODAY)
    assert result['observations'][0]['normalized'] == {'value': 42, 'unit': 'employees'}
    assert result['questions'][0]['key'] == 'business_identity'
    assert result['questions'][0]['state'] == 'missing_evidence'
    assert result['questions'][-1]['key'] == 'employee_count' and result['questions'][-1]['priority'] == 50
    assert result['support']['independence'] == 'not_established' and result['readiness'] == 'not_assessed'
    assert db.scalar(select(func.count(AuditEvent.id))) == audit_count
    assert db.scalar(select(func.count(EvidenceClaim.id)).where(EvidenceClaim.case_id == case.id)) == 0
    assert service.assess(db, case.id, batch['id'], assessment_date=date(2026, 9, 17))['content_hash'] != result['content_hash']


def test_required_factors_are_prioritized_without_acquisition_assumptions_for_marketing():
    profile = TargetProfile(purpose='marketing_introduction', employees=SizeRange(minimum=5, required=True))
    questions = service.questions(profile, [])
    assert all(q['key'] != 'company_type' for q in questions)
    employee = next(q for q in questions if q['key'] == 'employee_count')
    assert employee['priority'] == 80 and employee['state'] == 'missing_evidence'
    acquisition = service.questions(TargetProfile(purpose='acquisition_exploration'), [])
    assert next(q for q in acquisition if q['key'] == 'company_type')['required']


@pytest.mark.parametrize('corruption', ['proposal_case', 'packet', 'source_case', 'shape'])
def test_invalid_lineage_or_output_cannot_enter_assessment(override_db_session, tmp_path, corruption):
    db = override_db_session; case, batch = completed(db, tmp_path)
    attempt = db.scalar(select(ExtractionAttempt).where(ExtractionAttempt.case_id == case.id).order_by(ExtractionAttempt.id))
    proposal = db.get(ModelProposal, attempt.proposal_id)
    if corruption == 'proposal_case': proposal.case_id += 999
    elif corruption == 'packet': attempt.plan = {**attempt.plan, 'packet': {'excerpt': 'Tampered'}}
    elif corruption == 'source_case':
        from app.domain.models import CaseEvidence
        db.get(CaseEvidence, attempt.evidence_id).case_id += 999
    else: proposal.proposed_output = {'observations': 'wrong'}
    db.commit()
    result = service.assess(db, case.id, batch['id'], assessment_date=TODAY)
    assert result['observations'] == []
    assert result['attempt_outcomes'][0]['assessment'] in {'invalid_lineage', 'invalid_output_shape'}


def test_viewer_can_read_only_same_case_assessment(client, override_db_session, tmp_path):
    db = override_db_session; case, batch = completed(db, tmp_path)
    app.dependency_overrides[current_identity] = lambda: Identity(None, 'demo', 'viewer', None, 'Viewer', role='viewer')
    try:
        base = f'/api/research/cases/{case.id}/extraction-batches/{batch["id"]}/assessment'
        result = client.get(base + '?assessment_date=2026-09-16')
        assert result.status_code == 200 and result.json()['readiness'] == 'not_assessed'
        assert client.get(base + '?assessment_date=invalid').status_code == 422
        assert client.get(f'/api/research/cases/{case.id + 999}/extraction-batches/{batch["id"]}/assessment').status_code == 409
    finally:
        app.dependency_overrides.pop(current_identity, None)


def test_duplicates_competing_values_and_questions_preserve_all_observations(override_db_session, tmp_path):
    from test_source_passages import retained
    from app.research import extraction_batches as batches
    db = override_db_session
    case, _, _, _, settings = retained(db, tmp_path,
        b'<article>Acme employs 42 people. Other Acme employs 50 people.</article>')
    config = batches.BatchSettings(target_profile=TargetProfile(purpose='marketing_introduction'))
    prepared = batches.preview(db, case.id, config, settings)
    batch = create(db, case, config, settings, prepared)
    async def provider(plan, settings):
        a = {'field': 'employee_count', 'value': '42', 'quote': 'Acme employs 42 people.', 'certainty': 'source_reported'}
        b = {'field': 'employee_count', 'value': '50', 'quote': 'Other Acme employs 50 people.', 'certainty': 'source_reported'}
        return {'observations': [a, a, b], 'unresolved_questions': ['Are these different businesses?']}, TokenUsage(100, 50, 150)
    run(db, case, batch, settings, provider)
    result = service.assess(db, case.id, batch['id'], assessment_date=TODAY)
    assert len(result['observations']) == 3
    assert result['observations'][1]['duplicate_of'] == result['observations'][0]['ref']
    assert len(result['competing_clues']) == 1 and not result['competing_clues'][0]['confirmed_contradiction']
    assert len(result['competing_clues'][0]['observation_refs']) == 2
    assert result['support'] == {'distinct_content_hashes': 1, 'distinct_publisher_labels': 1, 'independence': 'not_established'}
    assert result['attempt_outcomes'][0]['model_questions'] == ['Are these different businesses?']


def test_pending_empty_and_tampered_batch_never_claim_completed_assessment(override_db_session, tmp_path):
    db = override_db_session
    case, _, _, _, settings, config, prepared = setup(db, tmp_path)
    batch = create(db, case, config, settings, prepared)
    result = service.assess(db, case.id, batch['id'], assessment_date=TODAY)
    assert result['batch_status'] == 'ready' and result['observations'] == []
    assert result['readiness'] == 'not_assessed'
    row = db.get(ExtractionBatch, batch['id'])
    row.plan_hash = '0' * 64; db.commit()
    with pytest.raises(ValueError, match='integrity'):
        service.assess(db, case.id, row.id, assessment_date=TODAY)
