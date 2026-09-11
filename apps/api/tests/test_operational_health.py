from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import pytest

from app.auth.service import Identity, current_identity
from app.core.config import Settings
from app.domain.models import AuditEvent, ModelProposal, SourceRefresh
from app.main import app
from app.ops.health import operational_readiness
from app.ops.telemetry import audit_write_failures
from app.ops.schema import alembic_config
from alembic.script import ScriptDirectory


def stamp_head(db):
    head = ScriptDirectory.from_config(alembic_config("sqlite://")).get_current_head()
    db.execute(text("create table if not exists alembic_version (version_num varchar(32) not null)"))
    db.execute(text("delete from alembic_version"))
    db.execute(text("insert into alembic_version (version_num) values (:head)"), {"head": head})
    db.commit()
    return head


def test_liveness_is_public_and_content_free(client):
    response = client.get("/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_is_operator_limited(client):
    app.dependency_overrides[current_identity] = lambda: Identity(None,"google","analyst",None,"Analyst",role="analyst")
    try:
        response = client.get("/api/operations/readiness")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(current_identity, None)


def test_readiness_reports_safe_aggregates(override_db_session, tmp_path):
    head = stamp_head(override_db_session)
    now = datetime.now(timezone.utc)
    override_db_session.add_all([
        SourceRefresh(source_key="source",jurisdiction="Utah",requested_by_key="operator",requested_by_name="Private Name",status="failed",record_limit=1,approved_cost_usd=1,actual_cost_usd=.25,contract_fingerprint="f"*64,error_code="timeout",started_at=now,finished_at=now),
        ModelProposal(case_id=1,task="ambiguity_analysis",provider="provider",model="private-model-name",prompt_version="v1",schema_version="v1",execution_outcome="failed",proposed_output=None,supported_evidence_ids=[],supported_claim_ids=[],input_tokens=1,output_tokens=1,total_tokens=2,latency_ms=1,cost_cents=7,error_class="unsafe body: secret"),
        AuditEvent(user_id=None,candidate_id=None,actor="Private Name",timestamp=now,action="authorization_denied",detail="private detail"),
    ])
    override_db_session.commit()

    payload = operational_readiness(override_db_session, Settings(database_url="sqlite://",evidence_storage_path=tmp_path), now)

    assert payload["status"] == "ready"
    assert payload["dependencies"]["schema"] == {"current_revision":head,"expected_revision":head,"at_head":True}
    assert payload["failures"]["source_refresh"] == {"timeout":1}
    assert payload["failures"]["model"]["redacted"] == 1
    assert payload["recorded_cost"]["source_refresh_usd"] == .25
    assert payload["recorded_cost"]["model_proposal_usd"] >= .07
    assert payload["audit"]["unattributed"] >= 1
    assert payload["audit"]["authorization_denials"] >= 1
    assert payload["content_boundaries"] == {"raw_evidence_included":False,"personal_identifiers_included":False,"provider_error_bodies_included":False,"record_identifiers_included":False}
    assert "Private Name" not in str(payload)
    assert "secret" not in str(payload)


def test_failed_audit_transaction_is_counted(override_db_session):
    before = audit_write_failures()
    override_db_session.add(AuditEvent(actor=None, action="invalid_fixture"))

    with pytest.raises(IntegrityError):
        override_db_session.commit()
    override_db_session.rollback()

    assert audit_write_failures() == before + 1
