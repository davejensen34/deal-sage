from uuid import uuid4

import pytest
from sqlalchemy import select

from app.domain.models import AuditEvent, CaseDecision
from app.research import development_briefs as service
from test_case_decisions import setup, payload, save


def development(**changes):
    return {'summary': 'A fictional continuity advisory introduction may be worth reviewing.',
            'unknowns': 'Ownership, sale intent, financials and contact permission are unknown.',
            'readiness': 'not_ready', 'readiness_reason': 'More research is needed before any communication.', **changes}


def contact(e, **changes):
    return {'source_id': e.id, 'recipient': 'Fictional business team', 'channel': 'website',
            'value': 'fictional', 'quote': 'An uncertain fictional business clue.',
            'public_business_use_reviewed': True, **changes}


def test_contact_and_readiness_boundaries(override_db_session):
    db = override_db_session; case, e, b = setup(db); _, foreign, _ = setup(db)
    for invalid in [development(readiness='reviewer_ready'), development(summary=' '*10),
                    development(contact=contact(e, public_business_use_reviewed=False)),
                    development(contact=contact(e, value='unreported@example.test'))]:
        with pytest.raises(ValueError):
            payload(outcome='create_development_brief', development=invalid)
    with pytest.raises(ValueError, match='required only'):
        payload(development=development())
    with pytest.raises(ValueError, match='required only'):
        payload(outcome='create_development_brief')
    for invalid in [contact(foreign), contact(e, quote='Another fictional quotation not retained.')]:
        with pytest.raises(ValueError, match='(source|quotation)'):
            save(db, case, payload(outcome='create_development_brief', development=development(contact=invalid)))
        db.rollback()
    r = save(db, case, payload(outcome='create_development_brief', development=development(readiness='reviewer_ready', contact=contact(e))))
    assert r['decision']['development']['readiness'] == 'reviewer_ready'


def test_handoff_preserves_frozen_basis_after_correction_and_source_changes(override_db_session):
    db = override_db_session; case, e, b = setup(db); key = uuid4()
    p = payload(outcome='create_development_brief', development=development(contact=contact(e)))
    first = save(db, case, p, key)
    original = service.handoff(db, case.id, first['id'])
    e.relevant_excerpt = 'Changed source, not the reviewed contact.'; db.commit()
    second = save(db, case, payload(expected_prior_id=first['id'], outcome='dismiss', change_reason='This case is no longer relevant to the stated purpose.'))
    historical = service.handoff(db, case.id, first['id'])
    assert historical['superseded_by_decision_id'] == second['id']
    assert historical['saved_brief'] == original['saved_brief']
    assert historical['contact_provenance'] == original['contact_provenance']
    assert historical['reviewer_decision'] == original['reviewer_decision']
    assert save(db, case, p, key) == first
    exported = service.text_export(historical)
    assert 'Ownership, sale intent, financials' in exported and 'An uncertain fictional business clue.' in exported
    assert 'model_observations' in exported and 'questions' in exported and 'Superseded by decision: '+str(second['id']) in exported
    assert 'Changed source' not in exported


def test_unknown_contact_and_legacy_request_recovery(override_db_session):
    db = override_db_session; case, e, b = setup(db); key = uuid4(); p = payload()
    first = save(db, case, p, key)
    assert 'development' not in db.get(CaseDecision, first['id']).content
    assert save(db, case, p, key) == first
    r = save(db, case, payload(expected_prior_id=first['id'], outcome='create_development_brief',
                             change_reason='Prepare a research-only internal handoff for later review.', development=development()))
    packet = service.handoff(db, case.id, r['id'])
    assert packet['contact_provenance'] is None
    assert 'No recipient selected.' in service.text_export(packet)
    with pytest.raises(ValueError): service.handoff(db, case.id, first['id'])


def test_export_permissions_case_boundary_and_audit(client, override_db_session):
    from app.main import app
    from app.auth.service import Identity, current_identity
    db = override_db_session; case, e, b = setup(db); other, _, _ = setup(db)
    r = save(db, case, payload(outcome='create_development_brief', development=development()))
    role = 'viewer'
    app.dependency_overrides[current_identity] = lambda: Identity(None, 'demo', 'test', None, 'Export Reviewer', role=role)
    url = f"/api/research/cases/{case.id}/decisions/{r['id']}/development-brief"
    try:
        assert client.get(url).status_code == 200
        assert client.post(url+'/export').status_code == 403
        role = 'analyst'
        assert client.get(url.replace(f'cases/{case.id}', f'cases/{other.id}')).status_code == 404
        response = client.post(url+'/export')
        assert response.status_code == 200 and response.headers['content-type'].startswith('text/plain')
        assert response.headers['cache-control'] == 'no-store'
        assert 'Nothing has been sent.' in response.text
        audit = db.scalar(select(AuditEvent).where(AuditEvent.action == 'development_brief_exported'))
        assert audit.actor == 'Export Reviewer' and audit.after_state['decision_id'] == r['id']
    finally:
        app.dependency_overrides.pop(current_identity, None)
