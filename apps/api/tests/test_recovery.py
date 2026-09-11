from datetime import datetime, timezone
from hashlib import sha256

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.database import Base
from app.domain.models import RawArtifact
from app.ops.recovery import verify_restored_evidence


@pytest.fixture
def recovery_db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


def add_artifact(db, root, content=b"retained evidence"):
    db.execute(text("create table if not exists alembic_version (version_num varchar(32) not null)"))
    if db.execute(text("select count(*) from alembic_version")).scalar_one() == 0:
        db.execute(text("insert into alembic_version (version_num) values ('test-head')"))
    digest = sha256(content).hexdigest()
    key = f"raw/test/{digest}"
    path = root / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    db.add(RawArtifact(content_hash=digest,source_key="test",source_record_id="1",canonical_url="https://example.test/1",retrieved_at=datetime.now(timezone.utc),media_type="text/plain",byte_size=len(content),storage_key=key,contract_fingerprint="c"*64,request_metadata={}))
    db.commit()
    return path


def test_recovery_verifies_database_to_artifact_integrity(recovery_db, tmp_path):
    add_artifact(recovery_db, tmp_path)

    result = verify_restored_evidence(recovery_db, tmp_path, "test-head")

    assert result.valid is True
    assert result.artifact_count == 1
    assert result.artifact_bytes == len(b"retained evidence")


def test_recovery_reports_changed_and_missing_artifacts(recovery_db, tmp_path):
    changed = add_artifact(recovery_db, tmp_path, b"changed evidence fixture")
    missing = add_artifact(recovery_db, tmp_path, b"another artifact")
    changed.write_bytes(b"changed")
    missing.unlink()

    result = verify_restored_evidence(recovery_db, tmp_path)

    assert result.valid is False
    assert result.hash_mismatches
    assert result.size_mismatches
    assert result.missing_keys


def test_recovery_rejects_unexpected_schema_revision(recovery_db, tmp_path):
    add_artifact(recovery_db, tmp_path, b"schema fixture")

    result = verify_restored_evidence(recovery_db, tmp_path, "different-head")

    assert result.valid is False
    assert result.schema_revision == "test-head"
