from datetime import datetime, timezone

import pytest

from app.domain.models import CuratedRecord, RawArtifact
from app.research.resolution import SignalResolutionService


def curated_record(db, subject_type: str, subject_key: str) -> CuratedRecord:
    artifact = RawArtifact(
        content_hash=f"{subject_key:0<64}"[:64],
        source_key=f"test-{subject_key}",
        source_record_id=subject_key,
        canonical_url=f"https://example.test/{subject_key}",
        retrieved_at=datetime.now(timezone.utc),
        media_type="application/json",
        byte_size=2,
        storage_key=f"raw/{subject_key}",
        contract_fingerprint="a" * 64,
        request_metadata={},
    )
    db.add(artifact)
    db.flush()
    record = CuratedRecord(
        artifact_id=artifact.id,
        subject_key=subject_key,
        subject_type=subject_type,
        parser_version="test-v1",
        schema_version="test-v1",
        status="curated",
        normalized_data={},
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_signal_can_resolve_to_an_existing_business(override_db_session):
    signal = curated_record(override_db_session, "transition_signal", "signal-resolved")
    business = curated_record(override_db_session, "business", "business-resolved")
    service = SignalResolutionService(override_db_session)

    resolution = service.begin(signal.id)
    finished = service.finish(
        resolution.id,
        "business_resolved",
        reason="Registry and filing evidence identify the candidate business.",
        resolved_by="deterministic-test",
        business_record_id=business.id,
    )

    assert finished.outcome == "business_resolved"
    assert finished.business_record_id == business.id


def test_signal_can_terminate_without_manufacturing_a_business(override_db_session):
    person = curated_record(override_db_session, "person", "person-no-business")
    service = SignalResolutionService(override_db_session)

    resolution = service.begin(person.id)
    finished = service.finish(
        resolution.id,
        "no_business_found",
        reason="Bounded registry and web research produced no supported business connection.",
        resolved_by="analyst-test",
    )

    assert finished.outcome == "no_business_found"
    assert finished.business_record_id is None
    with pytest.raises(ValueError, match="cannot be changed"):
        service.finish(
            resolution.id,
            "business_resolved",
            reason="Late unsupported guess",
            resolved_by="analyst-test",
        )


def test_relationship_unknown_requires_a_real_business_record(override_db_session):
    signal = curated_record(override_db_session, "transition_signal", "signal-unknown")
    unrelated_person = curated_record(override_db_session, "person", "not-a-business")
    service = SignalResolutionService(override_db_session)
    resolution = service.begin(signal.id)

    with pytest.raises(ValueError, match="existing curated business"):
        service.finish(
            resolution.id,
            "relationship_unknown",
            reason="A business clue exists but the relationship is not supported.",
            resolved_by="analyst-test",
            business_record_id=unrelated_person.id,
        )


def test_resolution_api_is_aggregate_only(client, override_db_session):
    signal = curated_record(override_db_session, "transition_signal", "private-signal")
    service = SignalResolutionService(override_db_session)
    resolution = service.begin(signal.id)
    service.finish(
        resolution.id,
        "no_business_found",
        reason="No supported match.",
        resolved_by="analyst-test",
    )

    response = client.get("/api/research/resolution-outcomes")
    assert response.status_code == 200
    assert response.json()["total"] >= 1
    assert "private-signal" not in str(response.json())
