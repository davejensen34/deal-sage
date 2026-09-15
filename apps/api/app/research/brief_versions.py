"""Bounded snapshots of existing research, with no synthesis calls or judgments."""
import json
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from app.domain.models import (ResearchCase, CaseEvidence, EvidenceClaim, ClaimContradiction,
    ResearchFrontierItem, ModelProposal, ModelProposalDisposition, AnalystConclusion,
    ExtractionAttempt, CaseBriefVersion, AuditEvent)
from app.research.extraction_attempts import digest, VERSION as EXTRACTION_VERSION
from app.research.lead_briefs import lead_brief
from app.research.transitions import case_transitions
from app.research.signal_freshness import case_signal_intake
from app.research.discovery_runs import utc

VERSION='case-brief-snapshot-v1'


def bounded(db, model, case_id, limit=200):
    rows=db.scalars(select(model).where(model.case_id==case_id).order_by(model.id).limit(limit+1)).all()
    if len(rows)>limit:
        raise ValueError(f'Brief scope exceeds {limit} {model.__tablename__} records; no partial version was created')
    return rows


def build(db, case_id):
    case=db.get(ResearchCase,case_id)
    if case is None: raise ValueError('Research case not found')
    evidence=bounded(db,CaseEvidence,case_id)
    claims=bounded(db,EvidenceClaim,case_id,500)
    conflicts=bounded(db,ClaimContradiction,case_id)
    frontier=bounded(db,ResearchFrontierItem,case_id)
    proposals=bounded(db,ModelProposal,case_id)
    dispositions=bounded(db,ModelProposalDisposition,case_id)
    conclusions=bounded(db,AnalystConclusion,case_id)
    attempts=bounded(db,ExtractionAttempt,case_id)
    transitions=case_transitions(db,case_id)
    brief=lead_brief(db,case,evidence,transitions,case_signal_intake(db,case_id),conflicts,frontier)
    sources=[{'id':e.id,'publisher':e.publisher,'canonical_url':e.canonical_url,'content_hash':e.content_hash,
        'classification':e.classification,'fact_fingerprint':digest(e.extracted_facts),'published_at':e.published_at,'retrieved_at':e.retrieved_at,
        'relevant_excerpt':(e.relevant_excerpt or '')[:2000],'excerpt_truncated':len(e.relevant_excerpt or '')>2000} for e in evidence]
    evidence_ids={e.id for e in evidence}
    linked={a.proposal_id:a for a in attempts if a.proposal_id}
    latest={d.proposal_id:d for d in dispositions}
    model_rows=[]
    for p in proposals:
        a=linked.get(p.id)
        if p.schema_version!=EXTRACTION_VERSION or p.execution_outcome!='completed' or not a or a.evidence_id not in evidence_ids:
            continue
        review=latest.get(p.id)
        model_rows.append({'id':p.id,'evidence_id':a.evidence_id,'provider':p.provider,'model':p.model,
            'observations':p.proposed_output['observations'],'unresolved_questions':p.proposed_output['unresolved_questions'],
            'source_hash':a.plan['packet']['content_hash'],'review_state':review.decision if review else 'unreviewed',
            'source_changed':any(a.plan['packet']['content_hash']!=e.content_hash or a.plan['packet']['excerpt']!=e.relevant_excerpt for e in evidence if e.id==a.evidence_id),
            'review_id':review.id if review else None})
    content={'method':VERSION,'case_id':case_id,'case_status':case.status,'source_brief':brief,'sources':sources,
        'transitions':transitions,'model_observations':model_rows,
        'model_scope':{'included':len(model_rows),'other_proposals':len(proposals)-len(model_rows)},
        'reviews':[{'id':d.id,'proposal_id':d.proposal_id,'analyst':d.analyst_name,'decision':d.decision,
            'rationale':d.rationale,'created_at':d.created_at,'corrected_output':d.corrected_output,
            'supporting_evidence_ids':d.supporting_evidence_ids,'supporting_claim_ids':d.supporting_claim_ids} for d in dispositions],
        'conclusions':[{'id':c.id,'analyst':c.analyst_name,'outcome':c.outcome,'statement':c.statement,'status':c.status} for c in conclusions],
        'questions':[{'id':f.id,'question':f.question,'rationale':f.rationale,'status':f.status,'priority':f.priority} for f in frontier],
        'conflicts':[{'id':c.id,'type':c.contradiction_type,'rationale':c.rationale,'status':c.status,
            'left_claim_id':c.left_claim_id,'right_claim_id':c.right_claim_id} for c in conflicts],
        # Fingerprints detect included claim changes without copying internal source metadata.
        'claim_records':[{'id':c.id,'fingerprint':digest({'evidence_id':c.evidence_id,'subject':c.subject_type,
            'predicate':c.predicate,'value':c.object_value,'relationship':c.relationship_semantics,
            'classification':c.classification,'status':c.status})} for c in claims]}
    encoded=json.dumps(content,sort_keys=True,default=str,ensure_ascii=False)
    if len(encoded.encode())>256000:
        raise ValueError('Brief exceeds the 256000-byte snapshot ceiling; no partial version was created')
    return json.loads(encoded)


def differences(previous, current):
    result={}
    for group in ['sources','claim_records','model_observations','reviews','conclusions','questions','conflicts']:
        before={r['id']:r for r in (previous or {}).get(group,[])}
        after={r['id']:r for r in current[group]}
        result[group]={'added':sorted(after.keys()-before.keys()),'removed':sorted(before.keys()-after.keys()),
            'changed':sorted(k for k in before.keys() & after.keys() if before[k]!=after[k])}
    return result


def latest(db, case_id):
    return db.scalar(select(CaseBriefVersion).where(CaseBriefVersion.case_id==case_id).order_by(CaseBriefVersion.version.desc()))


def preview(db, case_id):
    content=build(db,case_id);prior=latest(db,case_id);key=digest(content)
    return {'content':content,'content_hash':key,'latest_version':prior.version if prior else 0,
        'unchanged':bool(prior and prior.content_hash==key),'changes':differences(prior.content if prior else None,content)}


def view(row, include_content=True):
    result={'id':row.id,'version':row.version,'actor':row.actor,'created_at':utc(row.created_at),
        'content_hash':row.content_hash,'changes':row.changes}
    if include_content: result['content']=row.content
    return result


def save(db, case_id, *, request_key, expected_hash, expected_version, actor, actor_key, user_id=None):
    key=str(UUID(str(request_key)))
    locked=db.execute(update(ResearchCase).where(ResearchCase.id==case_id).values(updated_at=ResearchCase.updated_at))
    if locked.rowcount!=1:
        db.rollback();raise ValueError('Research case not found')
    prior=db.scalar(select(CaseBriefVersion).where(CaseBriefVersion.request_key==key))
    if prior:
        if (prior.case_id,prior.content_hash,prior.actor_key,prior.version)!=(case_id,expected_hash,actor_key,expected_version+1):
            db.rollback();raise ValueError('Request key belongs to another brief version')
        result=view(prior);db.commit();return result
    db.expire_all()
    prepared=preview(db,case_id)
    if prepared['content_hash']!=expected_hash or prepared['latest_version']!=expected_version:
        db.rollback();raise ValueError('Case inputs or latest version changed; preview again')
    if prepared['unchanged']:
        db.rollback();raise ValueError('No included inputs changed; the latest brief already captures them')
    row=CaseBriefVersion(case_id=case_id,version=expected_version+1,request_key=key,actor=actor,actor_key=actor_key,
        content_hash=expected_hash,content=prepared['content'],changes=prepared['changes'])
    try:
        db.add(row);db.flush()
        db.add(AuditEvent(actor=actor,user_id=user_id,action='case_brief_saved',after_state={
            'case_id':case_id,'brief_id':row.id,'version':row.version,'content_hash':expected_hash},
            detail='Saved existing evidence, model interpretation and human records; no new judgment or call.'))
        db.commit();db.refresh(row)
    except IntegrityError:
        db.rollback();raise ValueError('Concurrent brief version conflict; reload history') from None
    return view(row)
