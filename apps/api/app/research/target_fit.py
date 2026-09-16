"""Deterministic profile fit over normalized cited claims, not recommendation readiness.

The future reconciliation stage must supply a stable business key. This service
does not resolve identities, convert model proposals into facts, or judge truth.
"""
from datetime import date
from hashlib import sha256
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import select

from app.domain.models import CaseEvidence, ClaimContradiction, EvidenceClaim, ResearchCase


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)


class Categories(Contract):
    values: list[str] = Field(min_length=1, max_length=50)
    required: bool = True

    @model_validator(mode='after')
    def canonical(self):
        if any(not v or len(v)>100 or v!=v.strip().casefold() for v in self.values):
            raise ValueError('Use nonempty lowercase category labels of at most 100 characters')
        if len(set(self.values))!=len(self.values):
            raise ValueError('Duplicate category')
        return self


class SizeRange(Contract):
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    required: bool = False

    @model_validator(mode='after')
    def ordered(self):
        if self.minimum is None and self.maximum is None:
            raise ValueError('A size range needs at least one bound')
        if self.minimum is not None and self.maximum is not None and self.minimum>self.maximum:
            raise ValueError('Minimum exceeds maximum')
        return self


class TargetProfile(Contract):
    version: Literal['target-profile-v1'] = 'target-profile-v1'
    purpose: Literal['acquisition_exploration','marketing_introduction','succession_advisory']
    company_types: Categories | None = None
    industries: Categories | None = None
    excluded_industries: list[str] = Field(default_factory=list, max_length=50)
    employees: SizeRange | None = None
    annual_revenue_usd: SizeRange | None = None
    max_fact_age_days: int = Field(default=365, ge=1, le=3650)

    @model_validator(mode='after')
    def consistent(self):
        if self.company_types and not set(self.company_types.values)<={'private','public','nonprofit'}:
            raise ValueError('Unsupported company type')
        if self.excluded_industries:
            Categories(values=self.excluded_industries)
        if self.industries and set(self.industries.values)&set(self.excluded_industries):
            raise ValueError('An industry cannot be included and excluded')
        return self

    def effective_company_types(self):
        if self.company_types is not None:
            return self.company_types
        return Categories(values=['private']) if self.purpose=='acquisition_exploration' else None


class TargetFact(Contract):
    """Explicit normalization contract; a matching quotation alone is not truth."""
    version: Literal['target-fact-v1']
    business_key: str = Field(min_length=1, max_length=100)
    value: str | int
    unit: Literal['category','employees','USD/year']
    observed_on: str
    quote: str = Field(min_length=1, max_length=2000)
    period_start: str | None = None
    period_end: str | None = None

    @model_validator(mode='after')
    def typed(self):
        date.fromisoformat(self.observed_on)
        if not self.business_key.strip() or not self.quote.strip():
            raise ValueError('Business key and quote cannot be blank')
        if self.unit=='category':
            if type(self.value)!=str or not self.value or len(self.value)>100 or self.value!=self.value.strip().casefold():
                raise ValueError('Category must be a normalized label')
        elif type(self.value)!=int or self.value<0:
            raise ValueError('Size must be a nonnegative integer in the stated unit')
        if self.unit=='USD/year':
            start=date.fromisoformat(self.period_start or '')
            end=date.fromisoformat(self.period_end or '')
            if not 350 <= (end-start).days <= 371 or end>date.fromisoformat(self.observed_on):
                raise ValueError('Annual revenue requires a completed annual reporting period')
        elif self.period_start is not None or self.period_end is not None:
            raise ValueError('Reporting periods apply only to annual revenue')
        return self


UNITS={'company_type':'category','industry':'category','employee_count':'employees','annual_revenue':'USD/year'}


def assess_target_fit(db, case_id, business_key, profile: TargetProfile, *, assessment_date: date):
    """Read-only case-local fit. Unknowns/conflicts never become positive fit.

    Callers must use a reconciled business key, not a name match. Only asserted,
    direct source claims with exact retained citations enter factors. Rejected
    claim IDs and reasons remain visible; no model or analyst records are written.
    """
    if db.get(ResearchCase,case_id) is None:
        raise ValueError('Research case not found')
    if not isinstance(business_key,str) or not business_key.strip() or len(business_key)>100:
        raise ValueError('A stable business key is required')
    sources={e.id:e for e in db.scalars(select(CaseEvidence).where(CaseEvidence.case_id==case_id))}
    claims=db.scalars(select(EvidenceClaim).where(EvidenceClaim.case_id==case_id).order_by(EvidenceClaim.id)).all()
    conflicts=db.scalars(select(ClaimContradiction).where(ClaimContradiction.case_id==case_id,ClaimContradiction.status=='open')).all()
    contested={id for c in conflicts for id in (c.left_claim_id,c.right_claim_id)}
    accepted={k:[] for k in UNITS};ignored=[]
    for c in claims:
        if c.predicate not in UNITS:
            continue
        reason=None;source=sources.get(c.evidence_id)
        try:
            fact=TargetFact.model_validate(c.object_value)
        except (ValueError,ValidationError):
            reason='untyped_or_invalid_fact'
        else:
            if fact.business_key!=business_key:
                reason='different_business'
            elif c.status!='asserted' or c.subject_type!='business' or c.classification!='source_fact' or c.directness not in {'direct','direct_statement'}:
                reason='not_direct_source_assertion'
            elif source is None or source.classification!='source_fact' or not source.content_hash or fact.quote not in (source.relevant_excerpt or ''):
                reason='citation_not_grounded'
            elif fact.unit!=UNITS[c.predicate] or (c.predicate=='company_type' and fact.value not in {'private','public','nonprofit'}):
                reason='wrong_semantics_or_unit'
            else:
                # A newly published article cannot refresh an old revenue period.
                effective=date.fromisoformat(fact.period_end or fact.observed_on)
                age=(assessment_date-effective).days
                if date.fromisoformat(fact.observed_on)>assessment_date or not 0<=age<=profile.max_fact_age_days:
                    reason='outside_fact_window'
                else:
                    accepted[c.predicate].append({'claim_id':c.id,'evidence_id':c.evidence_id,
                        'content_hash':source.content_hash,'value':fact.value,'observed_on':fact.observed_on,
                        'period_start':fact.period_start,'period_end':fact.period_end,'quote':fact.quote})
        if reason:
            ignored.append({'claim_id':c.id,'reason':reason})

    factors=[]
    def factor(key, rule, excluded=False):
        observations=accepted[key]
        if rule is None:
            state='not_requested';required=False
        else:
            required=True if excluded else rule.required
            values={r['value'] for r in observations}
            if any(r['claim_id'] in contested for r in observations) or len(values)>1:
                state='conflicting'
            elif not values:
                state='unknown'
            else:
                value=next(iter(values))
                if excluded:matches=value not in rule.values
                elif isinstance(rule,Categories):matches=value in rule.values
                else:matches=(rule.minimum is None or value>=rule.minimum) and (rule.maximum is None or value<=rule.maximum)
                state='met' if matches else 'mismatch'
        factors.append({'factor':'excluded_industries' if excluded else key,'required':required,
            'state':state,'observations':observations})
    factor('company_type',profile.effective_company_types())
    factor('industry',profile.industries)
    factor('employee_count',profile.employees)
    factor('annual_revenue',profile.annual_revenue_usd)
    if profile.excluded_industries:
        factor('industry',Categories(values=profile.excluded_industries),True)
    hard=[f for f in factors if f['required']]
    # Conflicted hard evidence takes precedence over an apparent mismatch.
    status=('unresolved' if any(f['state']=='conflicting' for f in hard) else
        'not_fit' if any(f['state']=='mismatch' for f in hard) else
        'unresolved' if any(f['state']=='unknown' for f in hard) else
        'requirements_met' if hard else 'no_required_factors')
    content={'method':'target-fit-v1','case_id':case_id,'business_key':business_key,
        'assessment_date':assessment_date.isoformat(),'profile':profile.model_dump(),
        'effective_company_types':profile.effective_company_types().model_dump() if profile.effective_company_types() else None,
        'status':status,'factors':factors,'ignored_claims':ignored,
        'readiness':'not_assessed','boundary':'Target fit only; identity, transition, corroboration and purpose rationale still require assessment.'}
    content['content_hash']=sha256(json.dumps(content,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    return content
