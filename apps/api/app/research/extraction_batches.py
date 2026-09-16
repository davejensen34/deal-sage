"""Bounded retained-evidence investigation; no search, claims or recommendations.

One authorization freezes deterministic passage selection. Child extraction
attempts are the sole spend ledger and persist before every model call.
"""
from datetime import datetime, timedelta, timezone
import re
from uuid import UUID, uuid4, uuid5

from pydantic import Field
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from app.domain.models import AuditEvent, CaseEvidence, ExtractionAttempt, ExtractionBatch, ResearchCase
from app.research import extraction_attempts as extraction, source_passages as passages
from app.research.discovery_runs import utc
from app.research.target_fit import Contract, TargetProfile
from app.storage.local import LocalEvidenceStorage

VERSION = 'retained-extraction-batch-v1'
MAX_DOCUMENTS = 20


class BatchSettings(Contract):
    target_profile: TargetProfile
    max_calls: int = Field(default=2, ge=1, le=4)
    max_cost_cents: int = Field(default=6, ge=0, le=100)
    max_elapsed_seconds: int = Field(default=300, ge=30, le=900)


def relevance(text, profile):
    """Lexical research cues include negative statements; they never prove fit."""
    groups = {
        'transition': (5, ['retirement', 'retire', 'succession', 'successor', 'acquisition',
                           'died', 'death', 'ownership', 'sold', 'sale', 'leadership']),
        'business_context': (2, ['company', 'business', 'headquartered', 'operates', 'manufactures']),
    }
    if profile.industries or profile.excluded_industries:
        groups['industry'] = (4, (profile.industries.values if profile.industries else []) + profile.excluded_industries)
    if profile.employees:
        groups['employees'] = (3, ['employees', 'employs', 'workforce', 'staff'])
    if profile.annual_revenue_usd:
        groups['revenue'] = (3, ['revenue', 'sales', 'turnover'])
    if profile.effective_company_types():
        groups['company_type'] = (3, ['privately held', 'private company', 'public company', 'nonprofit', 'stock exchange'])
    found = {key: weight for key, (weight, terms) in groups.items()
             if any(re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text, re.I) for term in terms)}
    return sum(found.values()), list(found)


def preview(db, case_id, config, settings, *, storage=None):
    case = db.get(ResearchCase, case_id)
    if case is None or case.status != 'open':
        raise ValueError('An open research case is required')
    storage = storage or LocalEvidenceStorage(settings.evidence_storage_path)
    policy = extraction.policy(settings)
    if config.max_calls > policy['max_attempts'] or config.max_cost_cents > policy['max_cost_cents']:
        raise ValueError('Batch ceilings exceed configured case model limits')
    total = db.scalar(select(func.count(CaseEvidence.id)).where(CaseEvidence.case_id == case_id))
    evidence = db.scalars(select(CaseEvidence).where(CaseEvidence.case_id == case_id)
                          .order_by(CaseEvidence.id).limit(MAX_DOCUMENTS)).all()
    candidates, coverage = [], []
    for item in evidence:
        try:
            metadata, text = passages.document(db, case_id, item.id, storage)
        except ValueError:
            coverage.append({'evidence_id': item.id, 'content_hash': item.content_hash,
                             'status': 'unavailable_or_restricted'})
            continue
        coverage.append({**metadata, 'status': 'readable'})
        for index in range(metadata['passage_count']):
            passage = passages._passage(metadata, text, index)
            priority, reasons = relevance(passage['excerpt'], config.target_profile)
            # A document opening is a low-priority context fallback, not a match.
            if priority or index == 0:
                candidates.append({'evidence_id': item.id, 'index': index, 'priority': priority,
                    'reasons': reasons or ['opening_context'], 'excerpt_hash': passage['excerpt_hash']})
    candidates.sort(key=lambda x: (-x['priority'], x['evidence_id'], x['index']))
    selected, seen, duplicates = [], set(), 0
    for candidate in candidates:
        if candidate['excerpt_hash'] in seen:
            duplicates += 1
            continue
        seen.add(candidate['excerpt_hash'])
        if len(selected) >= config.max_calls:
            continue
        prepared = extraction.preview(db, case_id, candidate['evidence_id'], settings,
                                      passage_index=candidate['index'], storage=storage)
        selected.append({**candidate, **prepared})
    reservation = sum(step['plan']['policy']['reserved_cents'] for step in selected)
    if reservation > config.max_cost_cents:
        raise ValueError('Selected work exceeds the batch cost ceiling')
    plan = {'version': VERSION, 'case_id': case_id, 'settings': config.model_dump(), 'policy': policy,
            'steps': selected, 'coverage': coverage, 'total_evidence': total,
            'uninspected_evidence': max(0, total - len(evidence)), 'eligible_passages': len(candidates),
            'duplicate_passages': duplicates, 'unselected_unique_passages': len(seen) - len(selected),
            'planned_reservation_cents': reservation}
    return {'plan': plan, 'plan_hash': extraction.digest(plan)}


def child_key(row, index):
    return str(uuid5(UUID(row.request_key), f'{VERSION}:{index}'))


def child_actor_key(row):
    return extraction.digest([VERSION, row.id])


def require_batch(db, case_id, batch_id):
    row = db.get(ExtractionBatch, batch_id)
    if row is None or row.case_id != case_id:
        raise ValueError('Extraction batch not found in this case')
    return row


def view(db, row):
    keys = [child_key(row, i) for i in range(len(row.plan['steps']))]
    children = db.scalars(select(ExtractionAttempt).where(ExtractionAttempt.case_id == row.case_id,
                          ExtractionAttempt.actor_key == child_actor_key(row),
                          ExtractionAttempt.request_key.in_(keys)).order_by(ExtractionAttempt.id)).all()
    attempts = [extraction.attempt_view(db, item) for item in children]
    charged = sum(max(a['reserved_cents'], (a['proposal'] or {}).get('cost_cents') or 0) for a in attempts)
    return {'id': row.id, 'case_id': row.case_id, 'actor': row.actor, 'status': row.status, 'next_index': row.next_index,
            'stop_reason': row.stop_reason, 'plan': row.plan, 'plan_hash': row.plan_hash,
            'deadline': utc(row.deadline) if row.deadline else None,
            'recovery_after': utc(row.recovery_after) if row.recovery_after else None,
            'attempts': attempts, 'consumed_calls': len(attempts), 'accounted_cents': charged,
            'accounting': 'child reservations or higher measured estimates; not additional parent spend',
            'readiness': 'not_assessed'}


def audit(db, row, action, actor, user_id):
    db.add(AuditEvent(actor=actor, user_id=user_id, action=action,
                     after_state={'case_id': row.case_id, 'batch_id': row.id, 'status': row.status,
                                  'next_index': row.next_index, 'plan_hash': row.plan_hash}))


def create(db, case_id, config, settings, *, request_key, expected_hash, actor, actor_key, user_id=None, storage=None):
    key = str(UUID(str(request_key)))
    if db.execute(update(ResearchCase).where(ResearchCase.id == case_id)
                  .values(updated_at=ResearchCase.updated_at)).rowcount != 1:
        db.rollback(); raise ValueError('Research case not found')
    prior = db.scalar(select(ExtractionBatch).where(ExtractionBatch.request_key == key))
    if prior:
        if (prior.case_id, prior.actor_key, prior.plan_hash) != (case_id, actor_key, expected_hash):
            db.rollback(); raise ValueError('Request key belongs to another batch')
        result = view(db, prior); db.commit(); return result
    prepared = preview(db, case_id, config, settings, storage=storage)
    if prepared['plan_hash'] != expected_hash or not prepared['plan']['policy']['ready']:
        db.rollback(); raise ValueError('Batch scope or provider changed; preview again')
    row = ExtractionBatch(case_id=case_id, request_key=key, actor=actor, actor_key=actor_key,
                          **prepared, status='ready', next_index=0)
    try:
        db.add(row); db.flush(); audit(db, row, 'extraction_batch_authorized', actor, user_id)
        db.commit()
    except IntegrityError:
        db.rollback(); raise ValueError('Concurrent batch request identity conflict; reload history') from None
    return view(db, row)


def terminal(db, row, status, reason, actor, user_id):
    row.status, row.stop_reason, row.lease_key = status, reason, None
    audit(db, row, 'extraction_batch_' + status, actor, user_id)
    db.commit(); return view(db, row)


async def execute(db, case_id, batch_id, settings, *, actor, user_id=None, provider=None, storage=None):
    row = require_batch(db, case_id, batch_id)
    lease = str(uuid4())
    if db.execute(update(ExtractionBatch).where(ExtractionBatch.id == row.id, ExtractionBatch.status == 'ready')
                  .values(status='running', lease_key=lease)).rowcount != 1:
        db.rollback(); db.refresh(row); return view(db, row)
    db.refresh(row)
    now = datetime.now(timezone.utc)
    if row.deadline is None:
        row.deadline = now + timedelta(seconds=row.plan['settings']['max_elapsed_seconds'])
    row.recovery_after = now + timedelta(seconds=row.plan['policy']['timeout_seconds'] + 60)
    audit(db, row, 'extraction_batch_started', actor, user_id)
    db.commit()
    while True:
        # Hold this fence until the child commits its authorization. Cancellation
        # can prevent the next call, but cannot erase an already admitted call.
        locked = db.execute(update(ExtractionBatch).where(ExtractionBatch.id == row.id,
            ExtractionBatch.status == 'running', ExtractionBatch.lease_key == lease)
            .values(updated_at=ExtractionBatch.updated_at))
        if locked.rowcount != 1:
            db.rollback(); db.refresh(row); return view(db, row)
        db.refresh(row)
        if row.next_index >= len(row.plan['steps']):
            return terminal(db, row, 'completed', 'selected_work_exhausted', actor, user_id)
        step = row.plan['steps'][row.next_index]
        prior = db.scalar(select(ExtractionAttempt).where(ExtractionAttempt.request_key == child_key(row, row.next_index)))
        if prior is None:
            remaining = (utc(row.deadline) - datetime.now(timezone.utc)).total_seconds()
            if remaining < step['plan']['policy']['timeout_seconds']:
                return terminal(db, row, 'stopped', 'elapsed_time_ceiling', actor, user_id)
            usage = view(db, row)
            if usage['accounted_cents'] + step['plan']['policy']['reserved_cents'] > row.plan['settings']['max_cost_cents']:
                return terminal(db, row, 'stopped', 'cost_ceiling', actor, user_id)
        row.recovery_after = datetime.now(timezone.utc) + timedelta(seconds=row.plan['policy']['timeout_seconds'] + 60)
        db.flush()
        try:
            # Child work belongs to the batch, not a fabricated human action.
            # Parent authorization/start audits retain the real operator IDs.
            result = await extraction.execute(db, case_id, step['evidence_id'], settings,
                request_key=child_key(row, row.next_index), expected_hash=step['plan_hash'],
                passage_index=step['index'], actor=f'Extraction batch {row.id}', actor_key=child_actor_key(row),
                user_id=None, provider=provider, storage=storage)
        except ValueError:
            db.rollback()
            locked = db.execute(update(ExtractionBatch).where(ExtractionBatch.id == row.id,
                ExtractionBatch.status == 'running', ExtractionBatch.lease_key == lease)
                .values(updated_at=ExtractionBatch.updated_at))
            db.refresh(row)
            if locked.rowcount != 1:
                db.rollback(); return view(db, row)
            return terminal(db, row, 'stopped', 'child_admission_changed_or_unavailable', actor, user_id)
        # A process interruption between child publication and this checkpoint
        # is safe: its stable key replays the retained outcome after recovery.
        locked = db.execute(update(ExtractionBatch).where(ExtractionBatch.id == row.id,
            ExtractionBatch.status == 'running', ExtractionBatch.lease_key == lease)
            .values(updated_at=ExtractionBatch.updated_at))
        db.refresh(row)
        if locked.rowcount != 1:
            db.rollback(); return view(db, row)
        if result['status'] == 'running':
            db.commit(); return view(db, row)
        row.next_index += 1
        audit(db, row, 'extraction_batch_checkpoint', actor, user_id)
        db.commit()


def cancel(db, case_id, batch_id, *, actor, user_id=None):
    row = require_batch(db, case_id, batch_id)
    locked = db.execute(update(ExtractionBatch).where(ExtractionBatch.id == row.id,
        ExtractionBatch.status.in_(['ready', 'running'])).values(status='cancelled', lease_key=None))
    db.refresh(row)
    if locked.rowcount:
        audit(db, row, 'extraction_batch_cancelled', actor, user_id)
    db.commit(); return view(db, row)


def recover(db, case_id, batch_id, *, actor, user_id=None):
    row = require_batch(db, case_id, batch_id)
    now = datetime.now(timezone.utc)
    locked = db.execute(update(ExtractionBatch).where(ExtractionBatch.id == row.id,
        ExtractionBatch.status == 'running', ExtractionBatch.recovery_after <= now)
        .values(lease_key=None, status='ready').execution_options(synchronize_session=False))
    if locked.rowcount != 1:
        db.rollback(); raise ValueError('Batch is not interrupted or its recovery grace period has not elapsed')
    db.refresh(row)
    prior = db.scalar(select(ExtractionAttempt).where(ExtractionAttempt.request_key == child_key(row, row.next_index)))
    if prior and (prior.case_id != row.case_id or prior.actor_key != child_actor_key(row)
                  or prior.plan_hash != row.plan['steps'][row.next_index]['plan_hash']):
        db.rollback(); raise ValueError('Child request identity conflicts with this batch')
    if prior and prior.status == 'running':
        if utc(prior.recovery_after) > now:
            db.rollback(); raise ValueError('Child recovery grace period has not elapsed')
        # Fences late publication without another model call or a refunded slot.
        changed = db.execute(update(ExtractionAttempt).where(ExtractionAttempt.id == prior.id,
            ExtractionAttempt.status == 'running').values(status='unknown', error_code='interrupted_outcome_unknown'))
        if changed.rowcount:
            db.add(AuditEvent(actor=actor, user_id=user_id, action='extraction_recovered',
                             after_state={'case_id': case_id, 'attempt_id': prior.id}))
    audit(db, row, 'extraction_batch_recovered', actor, user_id)
    db.commit(); return view(db, row)
