"""Human workflow choices against an immutable brief, never research execution."""
from typing import Literal
from uuid import UUID
from pydantic import BaseModel,ConfigDict,Field,model_validator
from sqlalchemy import select,update
from app.domain.models import CaseDecision,CaseBriefVersion,ResearchCase,AuditEvent
from app.research.discovery_runs import utc
from app.research.development_briefs import DevelopmentInput, validate_contact


class DecisionInput(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    brief_version: int = Field(ge=1)
    expected_prior_id: int | None
    outcome: Literal['more_research','monitor','dismiss','create_development_brief']
    purpose: Literal['marketing_introduction','succession_advisory','acquisition_exploration']
    rationale: str = Field(min_length=10,max_length=2000)
    next_action: str = Field(min_length=10,max_length=1000)
    supporting_source_ids: list[int] = Field(default_factory=list,max_length=200)
    contradicting_source_ids: list[int] = Field(default_factory=list,max_length=200)
    change_reason: str = Field(default='',max_length=1000)
    development: DevelopmentInput | None = None

    @model_validator(mode='after')
    def coherent(self):
        if (self.outcome == 'create_development_brief') != (self.development is not None):
            raise ValueError('Development details are required only for a development brief')
        if len(self.rationale.strip())<10 or len(self.next_action.strip())<10:
            raise ValueError('Provide a meaningful rationale and next action')
        if self.expected_prior_id is not None and len(self.change_reason.strip())<10:
            raise ValueError('Changing a decision requires a reason')
        for ids in [self.supporting_source_ids,self.contradicting_source_ids]:
            if len(ids)!=len(set(ids)): raise ValueError('Source selections must not repeat')
        if set(self.supporting_source_ids)&set(self.contradicting_source_ids):
            raise ValueError('Select a source as supporting or contradicting; explain mixed evidence in the rationale')
        return self


def latest(db,case_id):
    return db.scalar(select(CaseDecision).where(CaseDecision.case_id==case_id).order_by(CaseDecision.id.desc()))


def view(row):
    return {'id':row.id,'case_id':row.case_id,'brief_id':row.brief_id,'prior_id':row.prior_id,
        'actor':row.actor,'created_at':utc(row.created_at),'decision':row.content}


def save(db,case_id,payload,*,request_key,actor,actor_key,user_id=None):
    # Omit the new optional field for legacy requests so their UUID recovery
    # still compares equal to decisions saved before development briefs existed.
    key=str(UUID(str(request_key)));content=payload.model_dump(exclude_none=True)
    content['expected_prior_id']=payload.expected_prior_id
    # Serialize the correction chain, including its first row, without changing
    # research status. Reviewing a stopped case must never restart execution.
    claim=db.execute(update(ResearchCase).where(ResearchCase.id==case_id).values(updated_at=ResearchCase.updated_at))
    if claim.rowcount!=1: raise ValueError('Case not found')
    prior_request=db.scalar(select(CaseDecision).where(CaseDecision.request_key==key))
    if prior_request:
        if (prior_request.case_id,prior_request.actor_key,prior_request.content)!=(case_id,actor_key,content):
            raise ValueError('Request key belongs to another decision')
        db.commit();return view(prior_request)
    db.expire_all()
    previous=latest(db,case_id)
    if (previous.id if previous else None)!=payload.expected_prior_id:
        raise ValueError('Decision changed; reload history before recording a correction')
    brief=db.scalar(select(CaseBriefVersion).where(CaseBriefVersion.case_id==case_id,CaseBriefVersion.version==payload.brief_version))
    if brief is None: raise ValueError('Saved brief version not found in this case')
    sources={s['id'] for s in brief.content['sources']}
    if not set(payload.supporting_source_ids+payload.contradicting_source_ids)<=sources:
        raise ValueError('Selected sources must belong to the saved brief version')
    if payload.development:
        validate_contact(payload.development, brief.content['sources'])
    row=CaseDecision(case_id=case_id,brief_id=brief.id,prior_id=payload.expected_prior_id,
        request_key=key,actor=actor,actor_key=actor_key,content=content)
    db.add(row);db.flush()
    db.add(AuditEvent(actor=actor,user_id=user_id,action='case_decision_recorded',after_state={
        'case_id':case_id,'decision_id':row.id,'brief_id':brief.id,'prior_id':row.prior_id},
        detail='Human workflow decision only; no research, monitoring, promotion or communication initiated.'))
    db.commit();db.refresh(row);return view(row)
