"""Personal monitoring reads and explicit history-preserving updates."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.service import Identity, current_identity, require_permission
from app.core.database import get_db
from app.domain.models import CaseMonitoring, ResearchCase
from app.research import case_monitoring as service
from app.research.extraction_attempts import digest

router = APIRouter(prefix='/api/monitoring', dependencies=[Depends(current_identity)])


def owner(identity):
    return digest([identity.provider, identity.subject])


class SaveMonitoring(BaseModel):
    request_key: UUID
    monitoring: service.MonitoringInput


@router.get('/cases')
def queue(scope: Literal['due', 'active', 'paused', 'all'] = 'due', page: int = Query(1, ge=1),
          db: Session = Depends(get_db), identity: Identity = Depends(current_identity)):
    return service.queue(db, owner(identity), scope=scope, page=page)


@router.get('/cases/{case_id}')
def history(case_id: int, page: int = Query(1, ge=1), db: Session = Depends(get_db),
            identity: Identity = Depends(current_identity)):
    if db.get(ResearchCase, case_id) is None: raise HTTPException(404, 'Case not found')
    key = owner(identity); current = service.latest(db, case_id, key)
    rows = db.scalars(select(CaseMonitoring).where(CaseMonitoring.case_id == case_id,
        CaseMonitoring.owner_key == key).order_by(CaseMonitoring.id.desc())
        .offset((page-1)*10).limit(11)).all()
    day = service.today()
    return {'latest': service.view(current, day) if current else None,
            'items': [service.view(r, day) for r in rows[:10]], 'has_next': len(rows) > 10, 'as_of': day.isoformat()}


@router.post('/cases/{case_id}')
def save(case_id: int, payload: SaveMonitoring, db: Session = Depends(get_db),
         identity: Identity = Depends(require_permission('personalize'))):
    try:
        return service.save(db, case_id, payload.monitoring, request_key=payload.request_key,
            owner_key=owner(identity), actor=identity.display_name, user_id=identity.user_id)
    except ValueError as exc:
        db.rollback(); raise HTTPException(409, str(exc)) from exc
