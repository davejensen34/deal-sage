import asyncio
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.ai.providers.base import TokenUsage
from app.auth.service import Identity, current_identity
from app.core.config import get_settings
from app.domain.models import CaseEvidence, EvidenceClaim, ExtractionAttempt, ExtractionBatch
from app.main import app
from app.research import extraction_batches as service, extraction_attempts as extraction
from app.research.cases import ResearchCaseService
from app.research.target_fit import TargetProfile, SizeRange
from test_source_passages import retained


@pytest.fixture(autouse=True)
def fixed_pricing(monkeypatch):
    original = extraction.policy
    monkeypatch.setattr(extraction, 'policy', lambda config: original(config, date(2026, 9, 16)))


def setup(db, tmp_path, **kw):
    case, item, artifact, storage, settings = retained(db, tmp_path)
    config = service.BatchSettings(target_profile=TargetProfile(purpose='marketing_introduction',
        employees=SizeRange(minimum=10)), **kw)
    prepared = service.preview(db, case.id, config, settings)
    return case, item, artifact, storage, settings, config, prepared


def create(db, case, config, settings, prepared, key=None):
    return service.create(db, case.id, config, settings, request_key=key or uuid4(),
        expected_hash=prepared['plan_hash'], actor='Operator', actor_key='operator')


async def empty_provider(plan, settings):
    return {'observations': [], 'unresolved_questions': ['Who owns the business?']}, TokenUsage(100, 50, 150)


def run(db, case, batch, settings, provider=empty_provider):
    return asyncio.run(service.execute(db, case.id, batch['id'], settings, actor='Operator', provider=provider))


def test_automatic_selection_prefers_later_context_and_freezes_coverage(override_db_session, tmp_path):
    db = override_db_session
    case, item, _, _, settings, config, prepared = setup(db, tmp_path)
    plan = prepared['plan']
    assert plan['steps'][0]['index'] == 1
    assert plan['steps'][0]['reasons'] == ['transition', 'employees']
    assert '42 people' in plan['steps'][0]['plan']['packet']['excerpt']
    assert plan['total_evidence'] == 1 and plan['uninspected_evidence'] == 0
    assert service.preview(db, case.id, config, settings) == prepared
    batch = create(db, case, config, settings, prepared)
    async def provider(plan, settings):
        observations = []
        if 'Fictional Acme employs 42 people.' in plan['packet']['excerpt']:
            observations.append({'field': 'employee_count', 'value': '42',
                'quote': 'Fictional Acme employs 42 people.', 'certainty': 'source_reported'})
        return {'observations': observations, 'unresolved_questions': []}, TokenUsage(100, 50, 150)
    result = run(db, case, batch, settings, provider)
    assert result['status'] == 'completed' and result['next_index'] == 2
    assert result['consumed_calls'] == 2 and result['accounted_cents'] == 0
    assert result['readiness'] == 'not_assessed'
    assert result['attempts'][0]['proposal']['output']['observations'][0]['value'] == '42'
    assert db.scalar(select(func.count(EvidenceClaim.id)).where(EvidenceClaim.case_id == case.id)) == 0
    assert item.relevant_excerpt == db.get(CaseEvidence, item.id).relevant_excerpt


def test_negative_cues_remain_research_clues_and_profile_changes_priority():
    profile = TargetProfile(purpose='marketing_introduction')
    assert service.relevance('No sale or ownership change occurred.', profile)[0] > 0
    assert service.relevance('A branch has four partners.', profile)[0] == 0
    sized = TargetProfile(purpose='marketing_introduction', employees=SizeRange(minimum=5))
    assert service.relevance('The workforce is unknown.', sized)[0] > service.relevance('The workforce is unknown.', profile)[0]


def test_create_replay_and_stale_selection(override_db_session, tmp_path):
    db = override_db_session
    case, item, _, _, settings, config, prepared = setup(db, tmp_path)
    key = uuid4(); batch = create(db, case, config, settings, prepared, key)
    assert create(db, case, config, settings, prepared, key) == batch
    item.publisher = 'Changed publisher'; db.commit()
    with pytest.raises(ValueError, match='preview again'):
        create(db, case, config, settings, prepared)
    result = run(db, case, batch, settings)
    assert result['status'] == 'stopped' and result['consumed_calls'] == 0
    assert result['stop_reason'] == 'child_admission_changed_or_unavailable'


def test_failed_child_consumes_slot_and_does_not_stop_other_frozen_work(override_db_session, tmp_path):
    db = override_db_session
    case, _, _, _, settings, config, prepared = setup(db, tmp_path)
    batch = create(db, case, config, settings, prepared); calls = []
    async def provider(plan, settings):
        calls.append(plan)
        if len(calls) == 1: raise RuntimeError('private provider message')
        return await empty_provider(plan, settings)
    result = run(db, case, batch, settings, provider)
    assert [a['status'] for a in result['attempts']] == ['failed', 'completed']
    assert len(calls) == 2 and result['consumed_calls'] == 2
    assert 'private provider message' not in str(result)
    assert run(db, case, batch, settings, provider) == result and len(calls) == 2


def test_cancel_during_call_keeps_admitted_result_but_prevents_next_call(override_db_session, tmp_path):
    db = override_db_session
    case, _, _, _, settings, config, prepared = setup(db, tmp_path)
    batch = create(db, case, config, settings, prepared); calls = []
    async def provider(plan, settings):
        calls.append(plan)
        service.cancel(db, case.id, batch['id'], actor='Operator')
        return await empty_provider(plan, settings)
    result = run(db, case, batch, settings, provider)
    assert result['status'] == 'cancelled' and len(calls) == 1
    assert result['attempts'][0]['status'] == 'completed'
    assert run(db, case, batch, settings, provider)['status'] == 'cancelled'


def test_interruption_recovery_skips_unknown_child_without_refund_or_repeat(override_db_session, tmp_path):
    db = override_db_session
    case, _, _, _, settings, config, prepared = setup(db, tmp_path)
    batch = create(db, case, config, settings, prepared)
    async def interrupted(plan, settings): raise asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError): run(db, case, batch, settings, interrupted)
    row = db.get(ExtractionBatch, batch['id'])
    child = db.scalar(select(ExtractionAttempt).where(ExtractionAttempt.case_id == case.id))
    assert row.status == child.status == 'running'
    with pytest.raises(ValueError, match='grace'): service.recover(db, case.id, row.id, actor='Operator')
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    row.recovery_after = past; child.recovery_after = past; db.commit()
    service.recover(db, case.id, row.id, actor='Operator')
    calls = []
    async def provider(plan, settings):
        calls.append(plan); return await empty_provider(plan, settings)
    result = run(db, case, batch, settings, provider)
    assert result['status'] == 'completed' and result['consumed_calls'] == 2 and len(calls) == 1
    assert [a['status'] for a in result['attempts']] == ['unknown', 'completed']


def test_duplicate_execution_does_not_spawn_second_runner(override_db_session, tmp_path):
    db = override_db_session
    case, _, _, _, settings, config, prepared = setup(db, tmp_path)
    batch = create(db, case, config, settings, prepared)
    async def provider(plan, settings):
        duplicate = await service.execute(db, case.id, batch['id'], settings, actor='Operator')
        assert duplicate['status'] == 'running'
        return await empty_provider(plan, settings)
    assert run(db, case, batch, settings, provider)['consumed_calls'] == 2


def test_elapsed_time_and_existing_case_capacity_stop_before_new_calls(override_db_session, tmp_path):
    db = override_db_session
    case, _, _, _, settings, config, prepared = setup(db, tmp_path)
    batch = create(db, case, config, settings, prepared)
    row = db.get(ExtractionBatch, batch['id'])
    row.deadline = datetime.now(timezone.utc) - timedelta(seconds=1); db.commit()
    result = run(db, case, batch, settings)
    assert result['stop_reason'] == 'elapsed_time_ceiling' and result['consumed_calls'] == 0
    second = create(db, case, config, settings, prepared)
    assert run(db, case, second, settings)['consumed_calls'] == 2
    third = create(db, case, config, settings, prepared)
    assert run(db, case, third, settings)['consumed_calls'] == 0


def test_unavailable_and_duplicate_evidence_preserve_denominator(override_db_session, tmp_path):
    db = override_db_session
    case, item, artifact, storage, settings, config, _ = setup(db, tmp_path)
    ResearchCaseService(db).add_evidence(case.id, source_mode='case_specific_research',
        canonical_url=item.canonical_url, publisher=item.publisher, source_type=item.source_type,
        content=storage.read(artifact.storage_key), relevant_excerpt=item.relevant_excerpt,
        extracted_facts={}, provenance={}, raw_artifact_id=artifact.id)
    result = service.preview(db, case.id, config, settings)['plan']
    assert result['total_evidence'] == 2 and result['duplicate_passages'] == 2
    assert len(result['steps']) == 2
    storage.delete(artifact.storage_key)
    prepared = service.preview(db, case.id, config, settings)
    assert len(prepared['plan']['coverage']) == 2 and prepared['plan']['steps'] == []
    batch = create(db, case, config, settings, prepared)
    result = run(db, case, batch, settings)
    assert result['consumed_calls'] == 0 and result['readiness'] == 'not_assessed'


def test_api_permissions_and_cross_case(client, override_db_session, tmp_path):
    db = override_db_session
    case, _, _, _, settings, config, _ = setup(db, tmp_path)
    other = ResearchCaseService(db).create_case('signal_first', {})
    role = 'viewer'
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[current_identity] = lambda: Identity(None, 'demo', 'test', None, 'User', role=role)
    base = f'/api/research/cases/{case.id}/extraction-batches'
    try:
        prepared = client.post(base + '/preview', json=config.model_dump()).json()
        payload = {'config': config.model_dump(), 'request_key': str(uuid4()), 'expected_hash': prepared['plan_hash']}
        assert client.post(base, json=payload).status_code == 403
        role = 'operator'
        batch = client.post(base, json=payload).json()
        url = base + '/' + str(batch['id'])
        assert client.get(f'/api/research/cases/{other.id}/extraction-batches/{batch["id"]}').status_code == 404
        role = 'viewer'
        for action in ['execute', 'cancel', 'recover']:
            assert client.post(url + '/' + action).status_code == 403
        role = 'operator'
        assert client.post(url + '/execute').json()['status'] == 'completed'
        assert client.get(url).json()['consumed_calls'] == 2
    finally:
        app.dependency_overrides.pop(get_settings, None); app.dependency_overrides.pop(current_identity, None)


def test_migration_reopen_and_retained_downgrade_guard(tmp_path):
    from alembic import command
    from app.ops.schema import alembic_config
    url = 'sqlite:///' + (tmp_path / 'batches.sqlite').as_posix()
    cfg = alembic_config(url); command.upgrade(cfg, 'c178a0b1d838'); command.upgrade(cfg, 'head')
    engine = create_engine(url)
    with Session(engine, expire_on_commit=False) as db:
        case, _, _, _, settings, config, prepared = setup(db, tmp_path / 'evidence')
        batch = create(db, case, config, settings, prepared)
        case_id = case.id
    with Session(engine, expire_on_commit=False) as db:
        result = asyncio.run(service.execute(db, case_id, batch['id'], settings, actor='Operator', provider=empty_provider))
        assert result['status'] == 'completed' and result['consumed_calls'] == 2
    with pytest.raises(RuntimeError, match='Cannot discard retained extraction batch'):
        command.downgrade(cfg, 'c178a0b1d838')
    engine.dispose()


def test_restart_after_child_publication_replays_without_call(override_db_session, tmp_path, monkeypatch):
    db = override_db_session
    case, _, _, _, settings, config, prepared = setup(db, tmp_path)
    batch = create(db, case, config, settings, prepared)
    original = service.audit
    def interrupted(db, row, action, actor, user_id):
        if action == 'extraction_batch_checkpoint': raise asyncio.CancelledError()
        return original(db, row, action, actor, user_id)
    monkeypatch.setattr(service, 'audit', interrupted)
    with pytest.raises(asyncio.CancelledError): run(db, case, batch, settings)
    db.rollback()
    row = db.get(ExtractionBatch, batch['id'])
    row.recovery_after = datetime.now(timezone.utc) - timedelta(seconds=1); db.commit()
    monkeypatch.setattr(service, 'audit', original)
    service.recover(db, case.id, row.id, actor='Operator')
    calls = []
    async def provider(plan, settings):
        calls.append(plan); return await empty_provider(plan, settings)
    result = run(db, case, batch, settings, provider)
    assert result['consumed_calls'] == 2 and len(calls) == 1


def test_reservations_and_invalid_usage_are_accounted_once(override_db_session, tmp_path):
    db = override_db_session
    case, _, _, _, settings, config, _ = setup(db, tmp_path, max_cost_cents=4)
    settings = settings.model_copy(update={'demo_mode': False, 'model_provider': 'openai',
        'openai_model': extraction.MODEL, 'openai_api_key': 'test-only'})
    prepared = service.preview(db, case.id, config, settings)
    assert prepared['plan']['planned_reservation_cents'] == 4
    batch = create(db, case, config, settings, prepared)
    async def overrun(plan, settings):
        return {'observations': [], 'unresolved_questions': []}, TokenUsage(100000, 0, 100000)
    result = run(db, case, batch, settings, overrun)
    assert result['consumed_calls'] == 1 and result['accounted_cents'] == 3
    assert result['stop_reason'] == 'cost_ceiling' and result['attempts'][0]['status'] == 'invalid'


def test_child_grace_and_old_runner_are_fenced_across_sessions(tmp_path):
    from app.core.database import Base
    engine = create_engine('sqlite:///' + (tmp_path / 'fences.sqlite').as_posix())
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        case, _, _, _, settings, config, prepared = setup(db, tmp_path / 'evidence')
        batch = create(db, case, config, settings, prepared)
        calls = []
        async def provider(plan, settings):
            calls.append(plan)
            with Session(engine, expire_on_commit=False) as other:
                row = other.get(ExtractionBatch, batch['id'])
                row.recovery_after = datetime.now(timezone.utc) - timedelta(seconds=1); other.commit()
                with pytest.raises(ValueError, match='Child recovery grace'):
                    service.recover(other, case.id, row.id, actor='Recovery operator')
                child = other.scalar(select(ExtractionAttempt).where(ExtractionAttempt.case_id == case.id))
                child.recovery_after = datetime.now(timezone.utc) - timedelta(seconds=1); other.commit()
                service.recover(other, case.id, row.id, actor='Recovery operator')
            return await empty_provider(plan, settings)
        result = run(db, case, batch, settings, provider)
        assert result['status'] == 'ready' and len(calls) == 1
        assert result['attempts'][0]['status'] == 'unknown'
        assert run(db, case, batch, settings)['status'] == 'completed'
    engine.dispose()


def test_bounded_document_inventory_and_unavailable_provider(override_db_session, tmp_path):
    db = override_db_session
    case, item, artifact, storage, settings, config, _ = setup(db, tmp_path)
    for _ in range(21):
        ResearchCaseService(db).add_evidence(case.id, source_mode='case_specific_research',
            canonical_url=item.canonical_url, publisher=item.publisher, source_type=item.source_type,
            content=storage.read(artifact.storage_key), relevant_excerpt=item.relevant_excerpt,
            extracted_facts={}, provenance={}, raw_artifact_id=artifact.id)
    prepared = service.preview(db, case.id, config, settings)
    assert len(prepared['plan']['coverage']) == 20 and prepared['plan']['uninspected_evidence'] == 2
    assert len(prepared['plan']['steps']) == 2
    batch = create(db, case, config, settings, prepared)
    changed = settings.model_copy(update={'demo_mode': False, 'model_provider': 'disabled'})
    result = run(db, case, batch, changed)
    assert result['status'] == 'stopped' and result['consumed_calls'] == 0
    with pytest.raises(ValueError, match='configured case'):
        service.preview(db, case.id, config.model_copy(update={'max_calls': 3}), settings)


def test_recovery_refuses_a_conflicting_child_identity(override_db_session, tmp_path):
    db = override_db_session
    case, _, _, _, settings, config, prepared = setup(db, tmp_path)
    batch = create(db, case, config, settings, prepared)
    row = db.get(ExtractionBatch, batch['id'])
    step = row.plan['steps'][0]
    child = ExtractionAttempt(request_key=service.child_key(row, 0), case_id=case.id,
        evidence_id=step['evidence_id'], actor='Other operator', actor_key='other', plan=step['plan'],
        plan_hash=step['plan_hash'], reserved_cents=0,
        recovery_after=datetime.now(timezone.utc) - timedelta(seconds=1))
    db.add(child); row.status = 'running'; row.recovery_after = child.recovery_after; db.commit()
    with pytest.raises(ValueError, match='identity conflicts'):
        service.recover(db, case.id, row.id, actor='Operator')
    db.refresh(child)
    assert child.status == 'running'
