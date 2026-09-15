from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.service import Identity, current_identity, require_permission
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.domain.models import FollowupRun, ResearchCase
from app.research import followups
from app.research.discovery_runs import run_view, execute_attempt, recover, digest
from app.api.discovery import ExecuteRun, RecoverRun

router=APIRouter(prefix='/api/followups',dependencies=[Depends(current_identity)])


class CreateFollowup(BaseModel):
    settings: followups.FollowupSettings
    request_key: UUID
    expected_hash: str = Field(pattern='^[0-9a-f]{64}$')


def load(db,run_id):
    row=db.get(FollowupRun,run_id)
    if row is None: raise HTTPException(404,'Follow-up not found')
    return row


@router.post('/cases/{case_id}/preview')
def preview(case_id:int,payload:followups.FollowupSettings,db:Session=Depends(get_db),
            settings:Settings=Depends(get_settings),identity:Identity=Depends(require_permission('review'))):
    try: return followups.preview(db,case_id,payload,settings)
    except ValueError as exc: raise HTTPException(409,str(exc)) from exc


@router.post('/cases/{case_id}')
def create(case_id:int,payload:CreateFollowup,db:Session=Depends(get_db),settings:Settings=Depends(get_settings),
           identity:Identity=Depends(require_permission('review'))):
    try:
        return run_view(db,followups.create(db,case_id,payload.settings,settings,request_key=payload.request_key,
            expected_hash=payload.expected_hash,actor=identity.display_name,
            actor_key=digest([identity.provider,identity.subject]),user_id=identity.user_id))
    except ValueError as exc:
        db.rollback();raise HTTPException(409,str(exc)) from exc


@router.get('/cases/{case_id}')
def history(case_id:int,db:Session=Depends(get_db)):
    if db.get(ResearchCase,case_id) is None: raise HTTPException(404,'Case not found')
    rows=db.scalars(select(FollowupRun).where(FollowupRun.case_id==case_id).order_by(FollowupRun.id.desc()).limit(10)).all()
    return {'items':[{'id':r.id,'question':r.plan['question'],'actor':r.actor,'status':r.status} for r in rows]}


@router.get('/runs/{run_id}')
def detail(run_id:int,db:Session=Depends(get_db)):
    return run_view(db,load(db,run_id))


@router.post('/runs/{run_id}/execute')
async def execute(run_id:int,payload:ExecuteRun,db:Session=Depends(get_db),settings:Settings=Depends(get_settings),
                  identity:Identity=Depends(require_permission('execute_ai'))):
    try:
        return await execute_attempt(db,load(db,run_id),settings,request_key=payload.request_key,
            expected_revision=payload.expected_revision,actor=identity.display_name,retry_last=payload.retry_last)
    except ValueError as exc:
        db.rollback();raise HTTPException(409,str(exc)) from exc


@router.post('/runs/{run_id}/recover')
def recover_run(run_id:int,payload:RecoverRun,db:Session=Depends(get_db),identity:Identity=Depends(require_permission('execute_ai'))):
    try: return recover(db,load(db,run_id),expected_revision=payload.expected_revision,actor=identity.display_name,user_id=identity.user_id)
    except ValueError as exc:
        db.rollback();raise HTTPException(409,str(exc)) from exc
