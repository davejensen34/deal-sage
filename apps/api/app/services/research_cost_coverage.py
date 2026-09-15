"""Inventory cost evidence without adding overlapping reservations and ledgers."""
from sqlalchemy import select
from app.domain.models import (ResearchQuery, ModelProposal, AIExecution, SourceRefresh,
    RetrievalAttempt, ExtractionAttempt, ResearchStep, FollowupAttempt)

def research_cost_coverage(db):
    queries=db.scalars(select(ResearchQuery)).all()
    proposals=db.scalars(select(ModelProposal)).all()
    executions=db.scalars(select(AIExecution)).all()
    refreshes=db.scalars(select(SourceRefresh)).all()
    retrievals=db.scalars(select(RetrievalAttempt)).all()
    extractions=db.scalars(select(ExtractionAttempt)).all()
    steps=db.scalars(select(ResearchStep)).all()
    linked=set(db.scalars(select(FollowupAttempt.step_id)).all())
    legacy_steps=[s for s in steps if s.id not in linked]
    # Zero-default model costs are not proof of free inference when usage was
    # absent. Report the recorded ledger and the measurement gap separately.
    rows=[
        {'name':'Search queries','records':len(queries),'recorded_amount':None,'unit':'USD',
         'missing_cost_records':sum(q.provider!='fixture' for q in queries),
         'scope':'Search query records store no monetary usage. Fixture queries are offline; real query spend is unknown. Attempt reservations are shown above.'},
        {'name':'Model proposals','records':len(proposals),'recorded_amount':sum(p.cost_cents for p in proposals),'unit':'USD cents',
         'missing_cost_records':sum(p.provider!='fixture' and (p.input_tokens is None or p.output_tokens is None) for p in proposals),
         'scope':'Recorded estimates, including legacy proposals; may overlap extraction reservations and research-step costs. Zero defaults without usage do not establish zero spend.'},
        {'name':'Extraction attempts without a proposal','records':sum(a.proposal_id is None for a in extractions),'recorded_amount':None,'unit':'USD',
         'missing_cost_records':sum(a.proposal_id is None for a in extractions),
         'scope':'Includes active or interrupted attempts. Reservations remain retained; an absent proposal is not a free call.'},
        {'name':'Legacy candidate AI executions','records':len(executions),'recorded_amount':None,'unit':'USD',
         'missing_cost_records':len(executions),
         'scope':'Execution records have no monetary cost column. Token counts cannot be priced without the historical model tariff.'},
        {'name':'Source refreshes','records':len(refreshes),'recorded_amount':round(sum(r.actual_cost_usd for r in refreshes),6),'unit':'USD',
         'missing_cost_records':sum(r.finished_at is None for r in refreshes),
         'scope':'Recorded source-refresh costs only; zero defaults on unfinished runs are not final spend. Not acquisition-wide or invoice reconciliation.'},
        {'name':'Document retrieval authorizations','records':len(retrievals),
         'recorded_amount':sum(r.plan.get('provider_cost_cents',0) for r in retrievals),'unit':'USD cents',
         'missing_cost_records':sum('provider_cost_cents' not in r.plan for r in retrievals),
         'scope':'Frozen provider-fee policy, not measured infrastructure/network spend; missing fee policies stay unknown.'},
        {'name':'Legacy research steps','records':len(legacy_steps),'recorded_amount':sum(s.cost_cents for s in legacy_steps),'unit':'USD cents',
         'missing_cost_records':sum(s.finished_at is None for s in legacy_steps),
         'scope':'Recorded step costs may duplicate proposal estimates. Follow-up-linked steps are excluded because they mirror reservations; other overlaps are not summed.'},
    ]
    return {'rows':rows,'grand_total':None,
        'boundary':'These ledgers overlap and are not additive. No complete billed-spend total is available. Local infrastructure, manual source files, external evaluation ledgers and unrecorded legacy acquisition costs are excluded. Missing costs are unknown, not zero.'}
