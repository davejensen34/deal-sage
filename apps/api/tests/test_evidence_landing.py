from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select

from app.domain.models import CuratedRecord, FieldLineage, RawArtifact, RunArtifact
from app.research.landing import CuratedSubject, EvidenceLanding, LandingEnvelope
from app.research.sources.colorado import parse_curated_record
from app.storage.local import LocalEvidenceStorage


def envelope(content: bytes = b'{"name":"Jordan Lee","state":"UT"}', fingerprint: str = "contract-v1") -> LandingEnvelope:
    return LandingEnvelope(source_key="test_signal_source",source_record_id="notice-1",canonical_url="https://example.test/notices/1",retrieved_at=datetime.now(timezone.utc),media_type="application/json",contract_fingerprint=fingerprint,request_metadata={"sample":"bounded"},content=content)


def signal_parser(content: bytes) -> list[CuratedSubject]:
    return [CuratedSubject(subject_key="notice-1:person",subject_type="person",data={"name":"Jordan Lee","state":"UT","business_id":None},lineage={"name":"$.name","state":"$.state"})]


def test_signal_first_landing_is_idempotent_and_replayable(override_db_session,tmp_path:Path):
    landing=EvidenceLanding(override_db_session,LocalEvidenceStorage(tmp_path))
    run=landing.start_run("test_signal_source","Utah","signal_first","contract-v1")
    first=landing.land(run,envelope(),signal_parser,"person-v1","subject-v1")
    repeated=landing.land(run,envelope(),signal_parser,"person-v1","subject-v1")
    replayed=landing.land(run,envelope(),signal_parser,"person-v2","subject-v1")

    assert first[0].id == repeated[0].id
    assert replayed[0].id != first[0].id
    assert first[0].subject_type == "person"
    assert first[0].normalized_data["business_id"] is None
    assert override_db_session.scalar(select(func.count(RawArtifact.id)).where(RawArtifact.source_key=="test_signal_source")) == 1
    assert override_db_session.scalar(select(func.count(RunArtifact.id)).where(RunArtifact.run_id==run.id)) == 1
    assert override_db_session.scalar(select(func.count(FieldLineage.id)).where(FieldLineage.curated_record_id==first[0].id)) == 2


def test_contract_drift_quarantines_without_publishing_subjects(override_db_session,tmp_path:Path):
    landing=EvidenceLanding(override_db_session,LocalEvidenceStorage(tmp_path))
    run=landing.start_run("test_signal_source","Utah","signal_first","contract-v1")
    records=landing.land(run,envelope(fingerprint="contract-v2"),signal_parser,"person-v1","subject-v1")

    assert records[0].status == "quarantined"
    assert records[0].subject_type == "unresolved"
    assert "fingerprint changed" in records[0].errors[0]
    assert run.status == "partial"


def test_retrieval_failure_is_recorded_without_sensitive_detail(override_db_session, tmp_path: Path):
    landing = EvidenceLanding(override_db_session, LocalEvidenceStorage(tmp_path))
    run = landing.start_run("source", "Colorado", "signal_first", "a" * 64)

    landing.fail_run(run, RuntimeError("token=must-not-be-persisted"))

    assert run.status == "failed"
    assert run.error == "RuntimeError"
    assert run.metrics["artifacts"] == 0


def test_local_evidence_storage_refuses_conflicting_rewrite(tmp_path:Path):
    storage=LocalEvidenceStorage(tmp_path)
    storage.save("raw/key",b"original")
    assert storage.save("raw/key",b"original").endswith("raw/key")
    try:
        storage.save("raw/key",b"changed")
    except ValueError as exc:
        assert "different content" in str(exc)
    else:
        raise AssertionError("Immutable evidence was overwritten")


def test_acquisition_api_exposes_outcomes_not_raw_content(client,override_db_session,tmp_path:Path):
    landing=EvidenceLanding(override_db_session,LocalEvidenceStorage(tmp_path))
    run=landing.start_run("api_signal_source","Colorado","signal_first","contract-v1")
    item=envelope()
    item=LandingEnvelope(source_key="api_signal_source",source_record_id=item.source_record_id,canonical_url=item.canonical_url,retrieved_at=item.retrieved_at,media_type=item.media_type,contract_fingerprint=item.contract_fingerprint,request_metadata={"authorization":"must-not-leak"},content=item.content)
    landing.land(run,item,signal_parser,"person-v1","subject-v1")

    response=client.get("/api/research/acquisition-runs")
    assert response.status_code == 200
    result=next(row for row in response.json() if row["source_key"]=="api_signal_source")
    assert result["discovery_strategy"] == "signal_first"
    assert result["artifact_count"] == 1
    assert result["curated_count"] == 1
    assert "authorization" not in str(result).lower()
    assert "Jordan Lee" not in str(result)


def test_colorado_fixture_curates_entity_and_keeps_agent_non_owner(override_db_session,tmp_path:Path):
    content=(Path(__file__).parent/"fixtures/colorado_entity.json").read_bytes()
    landing=EvidenceLanding(override_db_session,LocalEvidenceStorage(tmp_path))
    run=landing.start_run("colorado_fixture","Colorado","business_first","co-contract-v1")
    item=LandingEnvelope(source_key="colorado_fixture",source_record_id="20241999999",canonical_url="https://www.sos.state.co.us/biz/BusinessEntityDetail.do?fileId=20241999999",retrieved_at=datetime.now(timezone.utc),media_type="application/json",contract_fingerprint="co-contract-v1",request_metadata={"fixture":"representative"},content=content)
    records=landing.land(run,item,parse_curated_record,"colorado-entity-v1","curated-subject-v1")

    assert [record.subject_type for record in records] == ["business","relationship_assertion"]
    relationship=records[1].normalized_data
    assert relationship["relationship_type"] == "registered_agent"
    assert relationship["ownership_supported"] is False
