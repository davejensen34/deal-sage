"""Case-local batch authorization and execution; no recurring worker."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.service import Identity, current_identity, require_permission
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.research import extraction_batches as service
from app.research.extraction_attempts import digest

router = APIRouter(prefix='/api/research/cases/{case_id}/extraction-batches', dependencies=[Depends(current_identity)])


class CreateBatch(BaseModel):
    config: service.BatchSettings
    request_key: UUID
    expected_hash: str = Field(pattern='^[0-9a-f]{64}$')


@router.post('/preview')
def preview(case_id: int, config: service.BatchSettings, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    try:
        return service.preview(db, case_id, config, settings)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post('')
def create(case_id: int, payload: CreateBatch, db: Session = Depends(get_db), settings: Settings = Depends(get_settings),
           identity: Identity = Depends(require_permission('execute_ai'))):
    try:
        return service.create(db, case_id, payload.config, settings, request_key=payload.request_key,
            expected_hash=payload.expected_hash, actor=identity.display_name,
            actor_key=digest([identity.provider, identity.subject]), user_id=identity.user_id)
    except ValueError as exc:
        db.rollback(); raise HTTPException(409, str(exc)) from exc


@router.get('/{batch_id}')
def read(case_id: int, batch_id: int, db: Session = Depends(get_db)):
    try:
        return service.view(db, service.require_batch(db, case_id, batch_id))
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post('/{batch_id}/execute')
async def execute(case_id: int, batch_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings),
                  identity: Identity = Depends(require_permission('execute_ai'))):
    try:
        return await service.execute(db, case_id, batch_id, settings, actor=identity.display_name, user_id=identity.user_id)
    except ValueError as exc:
        db.rollback(); raise HTTPException(409, str(exc)) from exc


@router.post('/{batch_id}/cancel')
def cancel(case_id: int, batch_id: int, db: Session = Depends(get_db),
           identity: Identity = Depends(require_permission('execute_ai'))):
    try:
        return service.cancel(db, case_id, batch_id, actor=identity.display_name, user_id=identity.user_id)
    except ValueError as exc:
        db.rollback(); raise HTTPException(409, str(exc)) from exc


@router.post('/{batch_id}/recover')
def recover(case_id: int, batch_id: int, db: Session = Depends(get_db),
            identity: Identity = Depends(require_permission('execute_ai'))):
    try:
        return service.recover(db, case_id, batch_id, actor=identity.display_name, user_id=identity.user_id)
    except ValueError as exc:
        db.rollback(); raise HTTPException(409, str(exc)) from exc
