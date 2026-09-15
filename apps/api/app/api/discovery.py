"""Pilot discovery controls; source access and evidence review remain separate."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.service import Identity, current_identity, require_permission
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.domain.models import DiscoveryProfile, DiscoveryRun
from app.research.discovery_runs import DiscoverySettings, create_run, execute_attempt, preview, recover, run_view

router = APIRouter(prefix="/api/discovery", dependencies=[Depends(current_identity)])


class CreateRun(BaseModel):
    settings: DiscoverySettings
    request_key: UUID
    expected_hash: str = Field(min_length=64, max_length=64)
    profile_id: int | None = None


class ExecuteRun(BaseModel):
    request_key: UUID
    expected_revision: int = Field(ge=0)
    retry_last: bool = False


class RecoverRun(BaseModel):
    expected_revision: int = Field(ge=0)


def load(db, run_id):
    run = db.get(DiscoveryRun, run_id)
    if run is None:
        raise HTTPException(404, "Discovery run not found")
    return run


@router.get("/defaults")
def defaults(db: Session = Depends(get_db)):
    profile = db.scalar(select(DiscoveryProfile).order_by(DiscoveryProfile.id.desc()).limit(1))
    return {"profile_id": profile.id if profile else None,
            "settings": profile.settings if profile else DiscoverySettings().model_dump()}


@router.post("/defaults")
def save_defaults(payload: DiscoverySettings, db: Session = Depends(get_db),
                  identity: Identity = Depends(require_permission("operate_sources"))):
    profile = DiscoveryProfile(settings=payload.model_dump(), actor=identity.display_name)
    db.add(profile); db.commit(); db.refresh(profile)
    return {"profile_id": profile.id, "settings": profile.settings}


@router.post("/preview")
def preview_run(payload: DiscoverySettings, settings: Settings = Depends(get_settings),
                identity: Identity = Depends(require_permission("review"))):
    try:
        return preview(payload, settings)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/runs")
def new_run(payload: CreateRun, db: Session = Depends(get_db), settings: Settings = Depends(get_settings),
            identity: Identity = Depends(require_permission("review"))):
    try:
        return run_view(db, create_run(db, payload.settings, settings, request_key=payload.request_key,
            expected_hash=payload.expected_hash, actor=identity.display_name, profile_id=payload.profile_id))
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/runs")
def runs(page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    rows = db.scalars(select(DiscoveryRun).order_by(DiscoveryRun.id.desc()).offset((page-1)*10).limit(11)).all()
    return {"items": [{"id": r.id, "case_id": r.case_id, "status": r.status,
                       "objective": r.plan["settings"]["objective"]} for r in rows[:10]], "has_next": len(rows)>10}


@router.get("/runs/{run_id}")
def run_detail(run_id: int, db: Session = Depends(get_db)):
    return run_view(db, load(db, run_id))


@router.post("/runs/{run_id}/execute")
async def execute(run_id: int, payload: ExecuteRun, db: Session = Depends(get_db),
                  settings: Settings = Depends(get_settings), identity: Identity = Depends(require_permission("execute_ai"))):
    try:
        return await execute_attempt(db, load(db, run_id), settings, request_key=payload.request_key,
            expected_revision=payload.expected_revision, actor=identity.display_name, retry_last=payload.retry_last)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/runs/{run_id}/recover")
def recover_run(run_id: int, payload: RecoverRun, db: Session = Depends(get_db),
                identity: Identity = Depends(require_permission("execute_ai"))):
    try:
        return recover(db, load(db, run_id), expected_revision=payload.expected_revision,
            actor=identity.display_name, user_id=identity.user_id)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
