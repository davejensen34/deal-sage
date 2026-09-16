import asyncio
from datetime import date, datetime, timezone
from hashlib import sha256
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.ai.providers.base import TokenUsage
from app.auth.service import Identity, current_identity
from app.core.config import Settings, get_settings
from app.domain.models import EvidenceClaim, ExtractionAttempt, RawArtifact
from app.main import app
from app.research import extraction_attempts as extraction, source_passages as passages
from app.research.cases import ResearchCaseService
from app.research.retrieval import _bounded_text_excerpt
from app.storage.local import LocalEvidenceStorage


@pytest.fixture(autouse=True)
def frozen_pricing(monkeypatch):
    original = extraction.policy
    monkeypatch.setattr(extraction, 'policy', lambda config: original(config, date(2026, 9, 16)))


def retained(db, tmp_path, content=None, media='text/html'):
    content = content if content is not None else (
        '<article><p>' + 'Opening context. ' * 180 + '</p><p>'
        'Fictional Acme employs 42 people. Its owner plans to retire in 2027.'
        '</p></article>').encode()
    storage = LocalEvidenceStorage(tmp_path)
    digest = sha256(content).hexdigest()
    key = 'raw/' + str(uuid4())
    storage.save(key, content)
    case = ResearchCaseService(db).create_case('signal_first', {})
    url = 'https://example.test/fictional-discovery/' + str(case.id)
    artifact = RawArtifact(content_hash=digest, source_key=key, canonical_url=url,
        retrieved_at=datetime.now(timezone.utc), media_type=media, byte_size=len(content),
        storage_key=key, contract_fingerprint='0' * 64, request_metadata={})
    db.add(artifact); db.commit()
    item = ResearchCaseService(db).add_evidence(case.id, source_mode='case_specific_research',
        canonical_url=url, publisher='Fictional Gazette', source_type='other', content=content,
        relevant_excerpt=_bounded_text_excerpt(content, media), extracted_facts={}, provenance={},
        raw_artifact_id=artifact.id)
    config = Settings(_env_file=None, demo_mode=True, auth_mode='demo', evidence_storage_path=tmp_path)
    return case, item, artifact, storage, config


def test_later_context_has_reproducible_offsets_without_rewriting_evidence(override_db_session, tmp_path):
    db = override_db_session
    case, item, artifact, storage, config = retained(db, tmp_path)
    original = item.relevant_excerpt
    assert '42 people' not in original
    listing = passages.list_passages(db, case.id, item.id, storage)
    assert listing['passage_count'] == 2 and not listing['truncated']
    assert not listing['has_next'] and 'storage_key' not in str(listing)
    later = listing['items'][1]
    assert '42 people' in later['excerpt']
    assert later['start'] == 1800
    assert listing['items'][0]['excerpt'][-200:] == later['excerpt'][:200]
    text = passages.document(db, case.id, item.id, storage)[1]
    assert text[later['start']:later['end']] == later['excerpt']
    assert later['excerpt_hash'] == sha256(later['excerpt'].encode()).hexdigest()
    prepared = extraction.preview(db, case.id, item.id, config, passage_index=1)
    packet = prepared['plan']['packet']
    assert packet['excerpt'] == later['excerpt']
    assert packet['source_passage']['content_hash'] == artifact.content_hash
    assert extraction.preview(db, case.id, item.id, config, passage_index=1) == prepared
    assert 'source_passage' not in extraction.preview(db, case.id, item.id, config)['plan']['packet']
    assert item.relevant_excerpt == original


def test_selected_passage_execution_replay_and_citation_scope(override_db_session, tmp_path):
    db = override_db_session
    case, item, artifact, storage, config = retained(db, tmp_path)
    plan = extraction.preview(db, case.id, item.id, config, passage_index=1)
    calls = []
    async def provider(plan, config):
        calls.append(plan)
        return {'observations': [{'field': 'employee_count', 'value': '42',
            'quote': 'Fictional Acme employs 42 people.', 'certainty': 'source_reported'}],
            'unresolved_questions': []}, TokenUsage(100, 50, 150)
    args = dict(request_key=uuid4(), expected_hash=plan['plan_hash'], actor='Operator', actor_key='op',
                passage_index=1, provider=provider)
    result = asyncio.run(extraction.execute(db, case.id, item.id, config, **args))
    assert result['status'] == 'completed'
    assert result['packet']['source_passage']['index'] == 1
    # Replay uses the frozen packet even after the artifact becomes unavailable.
    storage.delete(artifact.storage_key)
    assert asyncio.run(extraction.execute(db, case.id, item.id, config, **args)) == result
    assert len(calls) == 1
    with pytest.raises(ValueError, match='another extraction'):
        asyncio.run(extraction.execute(db, case.id, item.id, config, **{**args, 'passage_index': 0}))
    assert db.scalar(select(func.count(EvidenceClaim.id)).where(EvidenceClaim.case_id == case.id)) == 0


def test_cross_passage_quote_is_not_accepted(override_db_session, tmp_path):
    db = override_db_session
    case, item, _, _, config = retained(db, tmp_path)
    plan = extraction.preview(db, case.id, item.id, config, passage_index=0)
    async def provider(plan, config):
        return {'observations': [{'field': 'employee_count', 'value': '42',
            'quote': 'Fictional Acme employs 42 people.', 'certainty': 'source_reported'}],
            'unresolved_questions': []}, TokenUsage(100, 50, 150)
    result = asyncio.run(extraction.execute(db, case.id, item.id, config, request_key=uuid4(),
        expected_hash=plan['plan_hash'], actor='Operator', actor_key='op', passage_index=0, provider=provider))
    assert result['status'] == 'invalid' and result['proposal']['output'] is None


@pytest.mark.parametrize('change', ['bytes', 'missing', 'size', 'hash', 'url', 'oversized'])
def test_artifact_integrity_failures_block_before_reservation(override_db_session, tmp_path, change):
    db = override_db_session
    case, item, artifact, storage, config = retained(db, tmp_path)
    plan = extraction.preview(db, case.id, item.id, config, passage_index=1)
    if change == 'bytes':
        storage._path(artifact.storage_key).write_bytes(b'corrupted')
    elif change == 'missing': storage.delete(artifact.storage_key)
    elif change == 'size': artifact.byte_size += 1
    elif change == 'hash': artifact.content_hash = 'f' * 64
    elif change == 'url': artifact.canonical_url += '/changed'
    elif change == 'oversized': storage._path(artifact.storage_key).write_bytes(b'x' * (passages.MAX_BYTES + 1))
    db.commit()
    with pytest.raises(ValueError, match='artifact'):
        asyncio.run(extraction.execute(db, case.id, item.id, config, request_key=uuid4(),
            expected_hash=plan['plan_hash'], actor='Operator', actor_key='op', passage_index=1))
    db.rollback()
    assert db.scalar(select(func.count(ExtractionAttempt.id)).where(ExtractionAttempt.case_id == case.id)) == 0


@pytest.mark.parametrize('content', [
    b'<meta property="article:content_tier" content="paid"><article>Not permitted</article>',
    b'<article>Visible</article><script>{"isAccessibleForFree":false}</script>',
    b'<article hidden>Hidden content</article><script>Executable content</script>',
])
def test_passages_reuse_restricted_and_hidden_content_guards(override_db_session, tmp_path, content):
    case, item, _, storage, _ = retained(override_db_session, tmp_path, content)
    with pytest.raises(ValueError, match='permitted readable'):
        passages.list_passages(override_db_session, case.id, item.id, storage)


def test_unicode_pagination_coverage_and_out_of_range(override_db_session, tmp_path):
    db = override_db_session
    text = 'Business café 🧭\n' * 8000
    case, item, _, storage, _ = retained(db, tmp_path, text.encode(), 'text/plain')
    first = passages.list_passages(db, case.id, item.id, storage)
    assert len(first['items']) == 10 and first['has_next'] and first['truncated']
    assert first['text_characters'] == len(text) and first['available_characters'] == 100000
    assert first['text_hash'] == sha256(text.encode()).hexdigest()
    final = passages.list_passages(db, case.id, item.id, storage, 6)
    assert len(final['items']) == 6 and not final['has_next']
    assert final['items'][-1]['end'] == 100000
    for section in first['items'] + final['items']:
        assert section['excerpt'] == text[section['start']:section['end']]
    for index in [-1, True, 56, '1']:
        with pytest.raises(ValueError, match='index'):
            passages.select_passage(db, case.id, item.id, storage, index)


def test_changed_selection_is_stale_before_any_attempt(override_db_session, tmp_path):
    db = override_db_session
    case, item, _, _, config = retained(db, tmp_path)
    plan = extraction.preview(db, case.id, item.id, config, passage_index=1)
    with pytest.raises(ValueError, match='preview again'):
        asyncio.run(extraction.execute(db, case.id, item.id, config, request_key=uuid4(),
            expected_hash=plan['plan_hash'], actor='Operator', actor_key='op', passage_index=0))
    assert db.scalar(select(func.count(ExtractionAttempt.id)).where(ExtractionAttempt.case_id == case.id)) == 0


def test_api_passage_selection_permissions_and_case_boundary(client, override_db_session, tmp_path):
    db = override_db_session
    case, item, _, _, config = retained(db, tmp_path)
    other = ResearchCaseService(db).create_case('signal_first', {})
    role = 'viewer'
    app.dependency_overrides[get_settings] = lambda: config
    app.dependency_overrides[current_identity] = lambda: Identity(None, 'demo', 'op', None, 'Reviewer', role=role)
    base = f'/api/research/cases/{case.id}/investigation/evidence/{item.id}'
    try:
        assert client.get(base + '/passages').json()['passage_count'] == 2
        assert client.get(base + '/passages?page=0').status_code == 422
        assert client.get(f'/api/research/cases/{other.id}/investigation/evidence/{item.id}/passages').status_code == 409
        preview = client.get(base + '/extraction-preview?passage_index=1').json()
        payload = {'request_key': str(uuid4()), 'expected_hash': preview['plan_hash'], 'passage_index': 1}
        assert client.post(base + '/extract', json=payload).status_code == 403
        role = 'operator'
        result = client.post(base + '/extract', json=payload)
        assert result.status_code == 200 and result.json()['status'] == 'completed'
        assert result.json()['packet']['source_passage']['index'] == 1
        assert client.post(base + '/extract', json={**payload, 'passage_index': True}).status_code == 422
        assert client.get(base + '/extraction-preview?passage_index=99').status_code == 409
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(current_identity, None)
