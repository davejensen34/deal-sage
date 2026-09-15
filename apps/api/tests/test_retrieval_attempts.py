import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.models import CaseEvidence, RawArtifact, RetrievalAttempt, SourceCandidate
from app.research.cases import ResearchCaseService
from app.research.retrieval import FixtureDocumentProvider, RetrievedDocument
from app.research.retrieval_attempts import execute, recover
from app.storage.local import LocalEvidenceStorage


def setup(db):
    case=ResearchCaseService(db).create_case("signal_first",{"max_documents":0})
    source=SourceCandidate(case_id=case.id,canonical_url="https://example.test/fictional-discovery/1",domain="example.test",
        publisher="Fictional source",likely_source_type="other",relevance_reason="Unverified",proposed_use="research",
        search_provider="fixture",access_decision="approved",access_decided_by="Test reviewer")
    db.add(source);db.commit();db.refresh(source)
    return case,source


def kwargs(source,tmp_path,**extra):
    return dict(request_key=uuid4(),expected_url=source.canonical_url,actor="Operator",storage=LocalEvidenceStorage(tmp_path),**extra)


def settings():
    return Settings(_env_file=None,demo_mode=True,auth_mode="demo",model_provider="disabled",web_search_provider="disabled")


def test_atomic_landing_dedup_and_key_replay_preserve_discovery_budget(override_db_session,tmp_path):
    db=override_db_session;case,source=setup(db);args=kwargs(source,tmp_path)
    first=asyncio.run(execute(db,case.id,source.id,settings(),**args))
    assert first["status"]=="succeeded" and first["evidence_id"]
    replay=asyncio.run(execute(db,case.id,source.id,settings(),**args))
    assert replay["id"]==first["id"]
    second=asyncio.run(execute(db,case.id,source.id,settings(),**kwargs(source,tmp_path)))
    assert second["evidence_id"]==first["evidence_id"]
    assert db.scalar(select(func.count(CaseEvidence.id)).where(CaseEvidence.case_id==case.id))==1
    evidence=db.get(CaseEvidence,first["evidence_id"])
    assert db.get(RawArtifact,evidence.raw_artifact_id).content_hash==evidence.content_hash
    db.refresh(case);assert case.research_budget["max_documents"]==0


def test_failures_consume_caps_without_provider_error_bodies(override_db_session,tmp_path):
    db=override_db_session;case,source=setup(db)
    for _ in range(3):
        outcome=asyncio.run(execute(db,case.id,source.id,settings(),**kwargs(source,tmp_path,
            provider=FixtureDocumentProvider(error=RuntimeError("private error body")))))
        assert outcome["status"]=="failed" and outcome["error_code"]=="retrieval_failed"
        assert "private error body" not in str(outcome)
    with pytest.raises(ValueError,match="ceiling"):
        asyncio.run(execute(db,case.id,source.id,settings(),**kwargs(source,tmp_path)))


def test_recovery_blocks_late_landing_and_concurrent_calls(override_db_session,tmp_path):
    db=override_db_session;case,source=setup(db)
    async def scenario():
        entered,release=asyncio.Event(),asyncio.Event()
        class Slow(FixtureDocumentProvider):
            async def retrieve(self,url,*,max_bytes):
                entered.set();await release.wait()
                return RetrievedDocument(url,b"Late fictional bytes","text/plain",datetime.now(timezone.utc))
        args=kwargs(source,tmp_path,provider=Slow())
        running=asyncio.create_task(execute(db,case.id,source.id,settings(),**args))
        await entered.wait()
        replay=await execute(db,case.id,source.id,settings(),**args)
        assert replay["status"]=="running"
        with pytest.raises(ValueError,match="active"):
            await execute(db,case.id,source.id,settings(),**kwargs(source,tmp_path))
        with pytest.raises(ValueError,match="not available"):
            recover(db,case.id,replay["id"],actor="Operator")
        row=db.get(RetrievalAttempt,replay["id"]);row.recovery_after=datetime.now(timezone.utc)-timedelta(seconds=1);db.commit()
        recover(db,case.id,row.id,actor="Operator")
        release.set();result=await running
        assert result["status"]=="unknown" and result["evidence_id"] is None
        assert db.scalar(select(func.count(CaseEvidence.id)).where(CaseEvidence.case_id==case.id))==0
    asyncio.run(scenario())


def test_atomic_rollback_after_evidence_failure(override_db_session,tmp_path,monkeypatch):
    db=override_db_session;case,source=setup(db)
    def fail(*args,**kwargs):raise RuntimeError("private failure context")
    monkeypatch.setattr(ResearchCaseService,"add_evidence",fail)
    args=kwargs(source,tmp_path,provider=FixtureDocumentProvider(RetrievedDocument(source.canonical_url,
        b"Unique bytes for a failed evidence transaction","text/plain",datetime.now(timezone.utc))))
    before=db.scalar(select(func.count(RawArtifact.id)))
    result=asyncio.run(execute(db,case.id,source.id,settings(),**args))
    assert result["status"]=="failed" and db.scalar(select(func.count(RawArtifact.id)))==before
    assert db.scalar(select(func.count(CaseEvidence.id)).where(CaseEvidence.case_id==case.id))==0


def test_api_requires_operator_access_and_rejects_changed_urls(client,override_db_session,tmp_path):
    from app.main import app
    from app.auth.service import Identity,current_identity
    from app.core.config import get_settings
    db=override_db_session;case,source=setup(db);role="analyst"
    app.dependency_overrides[current_identity]=lambda:Identity(None,"demo","test",None,"Operator",role=role)
    app.dependency_overrides[get_settings]=lambda:settings().model_copy(update={"evidence_storage_path":tmp_path})
    payload={"request_key":str(uuid4()),"expected_url":source.canonical_url}
    url=f"/api/research/cases/{case.id}/investigation/sources/{source.id}/retrieve"
    try:
        assert client.post(url,json=payload).status_code==403
        role="operator"
        assert client.post(url,json={**payload,"expected_url":"https://other.example.test/"}).status_code==409
        source.access_decision="blocked";db.commit()
        assert client.post(url,json=payload).status_code==409
        source.access_decision="approved";db.commit()
        assert client.post(url,json=payload).json()["status"]=="succeeded"
        source.canonical_url="https://public.example.test/real";db.commit()
        assert client.post(url,json={"request_key":str(uuid4()),"expected_url":source.canonical_url}).status_code==409
    finally:
        app.dependency_overrides.pop(current_identity,None);app.dependency_overrides.pop(get_settings,None)


def test_migration_and_restart_preserve_attempts(tmp_path):
    from alembic import command
    from app.ops.schema import alembic_config,upgrade_database
    url="sqlite:///"+(tmp_path/"retrieval.db").as_posix()
    command.upgrade(alembic_config(url),"c158a0b1d832");upgrade_database(url)
    engine=create_engine(url)
    with Session(engine) as db:
        case,source=setup(db);args=kwargs(source,tmp_path/"evidence")
        result=asyncio.run(execute(db,case.id,source.id,settings(),**args))
        case_id,source_id=case.id,source.id
    with Session(engine) as db:
        replay=asyncio.run(execute(db,case_id,source_id,settings(),**args))
        assert replay["id"]==result["id"] and replay["status"]=="succeeded"
    with pytest.raises(RuntimeError,match="Cannot discard"):
        command.downgrade(alembic_config(url),"c158a0b1d832")
    engine.dispose()
