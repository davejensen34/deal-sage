"""Personal, manual case follow-up dates with retained corrections."""
from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select, update

from app.domain.models import AuditEvent, CaseMonitoring, ResearchCase
from app.research.discovery_runs import utc


class MonitoringInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    expected_prior_id: int | None
    due_on: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    state: Literal['active', 'paused']
    question: str = Field(min_length=10, max_length=1000)
    reason: str = Field(min_length=10, max_length=1000)

    @model_validator(mode='after')
    def meaningful(self):
        date.fromisoformat(self.due_on)
        if min(len(self.question.strip()), len(self.reason.strip())) < 10:
            raise ValueError('Explain the monitoring question and reason in at least ten characters each')
        return self


def today():
    return datetime.now(timezone.utc).date()


def latest(db, case_id, owner_key):
    return db.scalar(select(CaseMonitoring).where(CaseMonitoring.case_id == case_id,
        CaseMonitoring.owner_key == owner_key).order_by(CaseMonitoring.id.desc()))


def view(row, as_of=None):
    return {'id': row.id, 'case_id': row.case_id, 'prior_id': row.prior_id,
            'actor': row.actor, 'recorded_at': utc(row.created_at), 'monitoring': row.content,
            'due': row.state == 'active' and row.due_on <= (as_of or today())}


def save(db, case_id, payload, *, request_key, owner_key, actor, user_id=None):
    key = str(UUID(str(request_key))); content = payload.model_dump()
    # Lock the existing case even for the first personal record. Concurrent
    # reminders cannot fork history, and stopped cases are not restarted.
    locked = db.execute(update(ResearchCase).where(ResearchCase.id == case_id)
                        .values(updated_at=ResearchCase.updated_at))
    if locked.rowcount != 1:
        raise ValueError('Case not found')
    prior_request = db.scalar(select(CaseMonitoring).where(CaseMonitoring.request_key == key))
    if prior_request:
        if (prior_request.case_id, prior_request.owner_key, prior_request.content) != (case_id, owner_key, content):
            raise ValueError('Request key belongs to another monitoring record')
        db.commit(); return view(prior_request)
    db.expire_all()
    prior = latest(db, case_id, owner_key)
    if (prior.id if prior else None) != payload.expected_prior_id:
        raise ValueError('Monitoring changed; reload your monitoring record before saving')
    row = CaseMonitoring(case_id=case_id, owner_key=owner_key, actor=actor,
        prior_id=payload.expected_prior_id, request_key=key, due_on=date.fromisoformat(payload.due_on),
        state=payload.state, content=content)
    db.add(row); db.flush()
    db.add(AuditEvent(actor=actor, user_id=user_id, action='case_monitoring_recorded',
        after_state={'case_id': case_id, 'monitoring_id': row.id, 'prior_id': row.prior_id},
        detail='Personal manual review date recorded; no research, promotion or notification started.'))
    db.commit(); db.refresh(row); return view(row)


def queue(db, owner_key, *, scope='due', page=1, as_of=None):
    day = as_of or today()
    # Filter the latest row per owner/case BEFORE applying date/state filters;
    # otherwise a paused or rescheduled item could resurrect an old due row.
    ids = select(func.max(CaseMonitoring.id)).where(CaseMonitoring.owner_key == owner_key).group_by(CaseMonitoring.case_id)
    base = select(CaseMonitoring).where(CaseMonitoring.id.in_(ids))
    due = (CaseMonitoring.state == 'active', CaseMonitoring.due_on <= day)
    total_due = db.scalar(select(func.count()).select_from(base.where(*due).subquery()))
    if scope == 'due': base = base.where(*due)
    elif scope in {'active', 'paused'}: base = base.where(CaseMonitoring.state == scope)
    rows = db.scalars(base.order_by(CaseMonitoring.due_on, CaseMonitoring.id)
                      .offset((page-1)*10).limit(11)).all()
    return {'items': [view(r, day) for r in rows[:10]], 'has_next': len(rows) > 10,
            'due_count': total_due, 'as_of': day.isoformat(), 'page': page}
