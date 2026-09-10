from datetime import datetime, timezone

from app.domain.models import AcquisitionRun, CaseEvidence, CuratedRecord, RawArtifact, ResearchCase, RunArtifact
from app.services import workflow_effectiveness as effectiveness_module


def test_effectiveness_reports_unattributed_candidates_instead_of_guessing(client):
    payload = client.get("/api/research/workflow-effectiveness").json()
    assert payload["candidate_total"] >= 18
    assert payload["unattributed_candidates"] >= 18
    assert payload["measurement_boundaries"]["unlinked_candidates_are_not_inferred"] is True
    assert payload["measurement_boundaries"]["cost_scope"] == "source_refresh_records_only"


def test_effectiveness_follows_durable_artifact_lineage(client, override_db_session):
    now = datetime.now(timezone.utc)
    run = AcquisitionRun(source_key="fixture_effectiveness", jurisdiction="Utah", discovery_strategy="hybrid", status="succeeded", contract_fingerprint="e" * 64, started_at=now, finished_at=now, metrics={})
    override_db_session.add(run)
    override_db_session.flush()
    artifact = RawArtifact(content_hash="f" * 64, source_key=run.source_key, source_record_id="safe-1", canonical_url="https://example.test/1", retrieved_at=now, media_type="application/json", byte_size=2, storage_key="raw/effectiveness/f", contract_fingerprint="e" * 64, request_metadata={})
    override_db_session.add(artifact)
    override_db_session.flush()
    override_db_session.add(RunArtifact(run_id=run.id, artifact_id=artifact.id))
    override_db_session.add(CuratedRecord(artifact_id=artifact.id, subject_key="business:1", subject_type="business", parser_version="fixture-v1", schema_version="fixture-v1", status="curated", normalized_data={}))
    case = ResearchCase(origin_strategy="hybrid", status="promoted_to_review", candidate_match_id=1, research_budget={}, confidence={})
    override_db_session.add(case)
    override_db_session.flush()
    override_db_session.add(CaseEvidence(case_id=case.id, raw_artifact_id=artifact.id, source_mode="fixture", canonical_url=artifact.canonical_url, publisher="Fixture", source_type="business_registry", retrieved_at=now, content_hash=artifact.content_hash, extracted_facts={}, provenance={}, classification="source_fact"))
    override_db_session.commit()

    payload = client.get("/api/research/workflow-effectiveness").json()
    row = next(item for item in payload["sources"] if item["source_key"] == run.source_key)
    assert row["attributed_candidates"] == 1
    assert row["curated_records"] == 1
    assert row["analyst_decisions"]["validated"] == 1
    assert payload["attributed_candidates"] >= 1
    assert payload["unattributed_candidates"] == payload["candidate_total"] - payload["attributed_candidates"]


def test_effectiveness_degrades_honestly_before_lineage_migration(client, monkeypatch):
    class LegacyInspector:
        def get_columns(self, table):
            assert table == "case_evidence"
            return [{"name": "id"}, {"name": "case_id"}]

    monkeypatch.setattr(effectiveness_module, "inspect", lambda bind: LegacyInspector())
    payload = client.get("/api/research/workflow-effectiveness").json()
    assert payload["attributed_candidates"] == 0
    assert payload["unattributed_candidates"] == payload["candidate_total"]
    assert payload["measurement_boundaries"]["durable_lineage_available"] is False
    assert payload["measurement_boundaries"]["lineage_unavailable_reason"] == "case_evidence_raw_artifact_link_not_migrated"
