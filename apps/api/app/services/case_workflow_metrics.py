"""Read-only case measures with explicit denominators and reservation scope."""
from collections import Counter
from statistics import median

from sqlalchemy import func, select

from app.domain.models import (CaseDecision, ResearchCase, DiscoveryAttempt,
                               FollowupAttempt, ExtractionAttempt)
from app.research.case_decisions import view


def case_workflow_metrics(db, page=1):
    if page < 1:
        raise ValueError('Page must be positive')
    # Select the latest shared decision before aggregating. Corrections and
    # repeat submissions must not inflate case or usefulness denominators.
    latest = select(func.max(CaseDecision.id)).group_by(CaseDecision.case_id)
    rows = db.scalars(select(CaseDecision).where(CaseDecision.id.in_(latest))
                      .order_by(CaseDecision.id.desc())).all()
    total = db.scalar(select(func.count(ResearchCase.id)))
    purposes = []
    for purpose in ('acquisition_exploration','marketing_introduction','succession_advisory'):
        decisions = [r.content for r in rows if r.content['purpose'] == purpose]
        feedback = [d.get('feedback') or {} for d in decisions]
        useful = sum(f.get('usefulness') == 'useful' for f in feedback)
        negative = sum(f.get('usefulness') == 'not_useful' for f in feedback)
        times = [f['review_seconds'] for f in feedback if f.get('review_seconds') is not None]
        purposes.append({'purpose':purpose, 'decisions':len(decisions),
            'useful':useful, 'not_useful':negative,
            'missing_judgments':len(decisions)-useful-negative,
            'assessed':useful+negative,
            'useful_percent':round(100*useful/(useful+negative),1) if useful+negative else None,
            'timed_reviews':len(times), 'median_review_seconds':median(times) if times else None})
    reservations = []
    for name, model in (('discovery',DiscoveryAttempt),('follow_up',FollowupAttempt),('extraction',ExtractionAttempt)):
        counts = db.execute(select(model.status,func.count(model.id),func.sum(model.reserved_cents))
                            .group_by(model.status)).all()
        reservations.append({'kind':name,'attempts':sum(r[1] for r in counts),
            'reserved_cents':sum(r[2] or 0 for r in counts),
            'outcomes':{r[0]:r[1] for r in counts}})
    return {'method':'case-workflow-measures-v1','total_cases':total,
        'cases_with_decisions':len(rows),'cases_without_decisions':total-len(rows),
        'decisions':dict(sorted(Counter(r.content['outcome'] for r in rows).items())),
        'purposes':purposes,'reservations':reservations,
        'items':[view(r) for r in rows[(page-1)*10:page*10]],'has_next':len(rows)>page*10,
        'measurement_scope':'Latest shared decision per case; all retained cases, not a selected evaluation cohort.',
        'cost_scope':'Retained discovery, follow-up and extraction attempt reservations only. Includes failures and interruptions; excludes legacy research, retrieval, source refresh and infrastructure. Actual spend is not measured here.'}
