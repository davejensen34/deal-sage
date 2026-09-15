"""Cross-service monitoring acceptance with no network or operational corpus."""
import asyncio
from copy import deepcopy
from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import Base
from app.domain.models import (CaseBriefVersion, CaseDecision, CaseMonitoring,
    CaseEvidence, EvidenceClaim, SourceCandidate, ResearchCase, ResearchFrontierItem,
    ModelProposalDisposition)
from app.research import (brief_versions, brief_comparisons, case_monitoring,
    case_decisions, followups, retrieval_attempts, extraction_attempts)
from app.research.cases import ResearchCaseService
from app.research.discovery_runs import execute_attempt
from app.research.search import FixtureSearchProvider, SearchResult, SearchService
from app.research.retrieval import FixtureDocumentProvider, RetrievedDocument
from app.ai.providers.base import TokenUsage
from app.storage.local import LocalEvidenceStorage


@pytest.mark.parametrize('find_source',[False,True],ids=['empty-followup','retained-source'])
def test_monitored_refresh_preserves_layers_and_requires_explicit_review(tmp_path,find_source):
    engine=create_engine('sqlite:///'+(tmp_path/'refresh.sqlite3').as_posix())
    Base.metadata.create_all(engine)
    config=Settings(_env_file=None,auth_mode='demo',demo_mode=True,
                    model_provider='disabled',web_search_provider='disabled')
    calls={'search':0,'document':0,'model':0}
    day=date.today()
    def snapshot(db,case_id):
        p=brief_versions.preview(db,case_id)
        return brief_versions.save(db,case_id,request_key=uuid4(),expected_hash=p['content_hash'],
            expected_version=p['latest_version'],actor='Fictional reviewer',actor_key='fixture')
    with Session(engine,expire_on_commit=False) as db:
        case=ResearchCaseService(db).create_case('signal_first',{'max_queries':0,'max_documents':0,'max_model_calls':0})
        case_id=case.id;budget=deepcopy(case.research_budget)
        first=snapshot(db,case_id)
        question='Has a source established business identity without assuming ownership?'
        monitor=case_monitoring.save(db,case_id,case_monitoring.MonitoringInput(
            expected_prior_id=None,due_on=day.isoformat(),state='active',question=question,
            reason='Keep this unresolved case for explicit manual research.'),
            request_key=uuid4(),owner_key='fixture',actor='Fictional reviewer')
        decision=case_decisions.save(db,case_id,case_decisions.DecisionInput(
            brief_version=1,expected_prior_id=None,outcome='monitor',purpose='acquisition_exploration',
            rationale='Identity and ownership are still unknown.',next_action=question),
            request_key=uuid4(),actor='Fictional reviewer',actor_key='fixture')
        settings=followups.FollowupSettings(question=question,rationale='Investigate the unresolved identity with retained provenance.',query='Fictional Acme business identity')
        preview=followups.preview(db,case_id,settings,config)
        run=followups.create(db,case_id,settings,config,request_key=uuid4(),expected_hash=preview['hash'],actor='Fictional reviewer',actor_key='fixture')
        url='https://example.test/fictional-discovery/refresh-184'
        class Search(FixtureSearchProvider):
            async def search(self,query,max_results):
                calls['search']+=1
                return [SearchResult(url=url,title='Fictional Acme',publisher='Fictional Gazette',relevance_reason='Unverified business clue',proposed_use='case_specific_research')] if find_source else []
        search_args=dict(request_key=uuid4(),expected_revision=run.revision,actor='Fixture operator',provider=Search())
        searched=asyncio.run(execute_attempt(db,run,config,**search_args))
        assert asyncio.run(execute_attempt(db,run,config,**search_args))==searched
        assert searched['attempts'][0]['result_count']==int(find_source)
        if find_source:
            source=db.scalar(select(SourceCandidate).where(SourceCandidate.case_id==case_id))
            SearchService(db).decide_access(source.id,decision='approved',reason='Permitted fictional fixture; approval does not verify content.',decided_by='Fictional reviewer')
            excerpt='Fictional Acme makes widgets. Ownership and sale intent remain unknown.'
            class Document(FixtureDocumentProvider):
                async def retrieve(self,url,*,max_bytes):
                    calls['document']+=1
                    return RetrievedDocument(url,excerpt.encode(),'text/plain',datetime.now(timezone.utc))
            args=dict(request_key=uuid4(),expected_url=url,actor='Fixture operator',provider=Document(),storage=LocalEvidenceStorage(tmp_path/'evidence'))
            retrieved=asyncio.run(retrieval_attempts.execute(db,case_id,source.id,config,**args))
            assert retrieved['status']=='succeeded'
            assert asyncio.run(retrieval_attempts.execute(db,case_id,source.id,config,**args))==retrieved
            evidence_id=retrieved['evidence_id']
            async def model(plan,settings):
                calls['model']+=1
                return {'observations':[{'field':'business_name','value':'Fictional Acme','quote':'Fictional Acme makes widgets.','certainty':'source_reported'}],
                        'unresolved_questions':['Who owns this business?']},TokenUsage(100,50,150)
            prepared=extraction_attempts.preview(db,case_id,evidence_id,config)
            args=dict(request_key=uuid4(),expected_hash=prepared['plan_hash'],actor='Fixture operator',actor_key='fixture',provider=model)
            extracted=asyncio.run(extraction_attempts.execute(db,case_id,evidence_id,config,**args))
            assert extracted['status']=='completed'
            assert asyncio.run(extraction_attempts.execute(db,case_id,evidence_id,config,**args))==extracted
        assert calls=={'search':1,'document':int(find_source),'model':int(find_source)}
        second=snapshot(db,case_id)
        comparison=brief_comparisons.compare(db,case_id,1,2)
        assert comparison['groups']['sources']['counts']['added']==int(find_source)
        assert comparison['groups']['model_observations']['counts']['added']==int(find_source)
        assert comparison['groups']['questions']['counts']['added']>=1
        # An empty search still records the question; neither empty nor positive
        # provider output establishes ownership, answers it, or completes review.
        assert db.get(ResearchFrontierItem,run.frontier_id).status=='pending'
        assert case_monitoring.latest(db,case_id,'fixture').id==monitor['id']
        assert case_monitoring.queue(db,'fixture',as_of=day)['due_count']==1
        assert case_decisions.latest(db,case_id).id==decision['id']
        assert db.scalar(select(func.count(ModelProposalDisposition.id)))==0
        assert db.scalar(select(func.count(EvidenceClaim.id)))==0
        assert case.candidate_match_id is None and case.research_budget==budget
        reviewed=case_decisions.save(db,case_id,case_decisions.DecisionInput(
            brief_version=2,expected_prior_id=decision['id'],outcome='more_research',purpose='acquisition_exploration',
            rationale='Fictional refresh leaves ownership and sale intent unknown.',next_action=question,
            change_reason='Explicit review of the newly retained brief version.',
            feedback={'usefulness':'not_assessed','reason':'Automated fixture, not a human quality judgment.'}),
            request_key=uuid4(),actor='Fictional reviewer',actor_key='fixture')
        assert case_monitoring.queue(db,'fixture',as_of=day)['due_count']==1
        paused=case_monitoring.save(db,case_id,case_monitoring.MonitoringInput(
            expected_prior_id=monitor['id'],due_on=day.isoformat(),state='paused',question=question,
            reason='Explicit pause after fictional review; question remains unresolved.'),
            request_key=uuid4(),owner_key='fixture',actor='Fictional reviewer')
        assert case_monitoring.queue(db,'fixture',as_of=day)['due_count']==0
    with Session(engine) as db:
        assert db.get(CaseBriefVersion,first['id']).content==first['content']
        assert db.get(CaseBriefVersion,second['id']).content==second['content']
        assert brief_comparisons.compare(db,case_id,1,2)==comparison
        assert db.get(CaseDecision,decision['id']).content==decision['decision']
        assert case_decisions.latest(db,case_id).id==reviewed['id']
        assert db.get(CaseMonitoring,monitor['id']).state=='active'
        assert case_monitoring.latest(db,case_id,'fixture').id==paused['id']
        assert db.get(ResearchCase,case_id).research_budget==budget
        assert db.scalar(select(func.count(CaseEvidence.id)))==int(find_source)
    engine.dispose()
