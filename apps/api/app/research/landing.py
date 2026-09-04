from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import AcquisitionRun, CuratedRecord, FieldLineage, RawArtifact, RunArtifact
from app.storage.base import EvidenceStorage


@dataclass(frozen=True)
class LandingEnvelope:
    source_key: str
    source_record_id: str | None
    canonical_url: str
    retrieved_at: datetime
    media_type: str
    contract_fingerprint: str
    request_metadata: dict[str, Any]
    content: bytes


@dataclass(frozen=True)
class CuratedSubject:
    subject_key: str
    subject_type: str
    data: dict[str, Any]
    lineage: dict[str, str]


Parser = Callable[[bytes], list[CuratedSubject]]


class EvidenceLanding:
    """Persist immutable transport evidence before publishing any normalized result."""

    def __init__(self, db: Session, storage: EvidenceStorage):
        self.db = db
        self.storage = storage

    def start_run(self, source_key: str, jurisdiction: str, discovery_strategy: str, contract_fingerprint: str) -> AcquisitionRun:
        if discovery_strategy not in {"signal_first", "business_first", "hybrid"}:
            raise ValueError("Unsupported discovery strategy")
        run = AcquisitionRun(source_key=source_key, jurisdiction=jurisdiction, discovery_strategy=discovery_strategy, contract_fingerprint=contract_fingerprint)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def land(self, run: AcquisitionRun, envelope: LandingEnvelope, parser: Parser, parser_version: str, schema_version: str) -> list[CuratedRecord]:
        digest = sha256(envelope.content).hexdigest()
        artifact = self.db.scalar(select(RawArtifact).where(RawArtifact.source_key == envelope.source_key, RawArtifact.content_hash == digest))
        if artifact is None:
            source_bucket = sha256(envelope.source_key.encode()).hexdigest()[:12]
            storage_key = f"raw/{source_bucket}/{digest}"
            self.storage.save(storage_key, envelope.content)
            artifact = RawArtifact(content_hash=digest, source_key=envelope.source_key, source_record_id=envelope.source_record_id, canonical_url=envelope.canonical_url, retrieved_at=envelope.retrieved_at, media_type=envelope.media_type, byte_size=len(envelope.content), storage_key=storage_key, contract_fingerprint=envelope.contract_fingerprint, request_metadata=envelope.request_metadata)
            self.db.add(artifact)
            self.db.flush()
        if self.db.scalar(select(RunArtifact).where(RunArtifact.run_id == run.id, RunArtifact.artifact_id == artifact.id)) is None:
            self.db.add(RunArtifact(run_id=run.id, artifact_id=artifact.id))
        try:
            if envelope.contract_fingerprint != run.contract_fingerprint:
                raise ValueError("Source contract fingerprint changed during acquisition")
            existing = self.db.scalars(select(CuratedRecord).where(CuratedRecord.artifact_id == artifact.id, CuratedRecord.parser_version == parser_version)).all()
            if existing:
                self._finish_run(run)
                return existing
            subjects = parser(envelope.content)
            if not subjects:
                raise ValueError("Parser produced no subjects")
        except Exception as exc:
            # Quarantine is itself a durable parser outcome; raw bytes remain
            # replayable under a corrected parser without another source fetch.
            record = CuratedRecord(artifact_id=artifact.id, subject_key="unresolved", subject_type="unresolved", parser_version=parser_version, schema_version=schema_version, status="quarantined", errors=[str(exc)])
            self.db.add(record)
            self._finish_run(run)
            self.db.refresh(record)
            return [record]
        records: list[CuratedRecord] = []
        for subject in subjects:
            record = CuratedRecord(artifact_id=artifact.id, subject_key=subject.subject_key, subject_type=subject.subject_type, parser_version=parser_version, schema_version=schema_version, status="curated", normalized_data=subject.data)
            self.db.add(record)
            self.db.flush()
            for field_name, raw_path in subject.lineage.items():
                value = subject.data.get(field_name)
                value_hash = sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()
                self.db.add(FieldLineage(curated_record_id=record.id, field_name=field_name, raw_path=raw_path, source_value_hash=value_hash))
            records.append(record)
        self._finish_run(run)
        return records

    def _finish_run(self, run: AcquisitionRun) -> None:
        self.db.flush()
        artifact_ids = select(RunArtifact.artifact_id).where(RunArtifact.run_id == run.id)
        artifact_count = self.db.scalar(select(func.count(RunArtifact.id)).where(RunArtifact.run_id == run.id)) or 0
        curated_count = self.db.scalar(select(func.count(CuratedRecord.id)).where(CuratedRecord.artifact_id.in_(artifact_ids), CuratedRecord.status == "curated")) or 0
        quarantined_count = self.db.scalar(select(func.count(CuratedRecord.id)).where(CuratedRecord.artifact_id.in_(artifact_ids), CuratedRecord.status == "quarantined")) or 0
        run.status = "partial" if quarantined_count else "succeeded"
        run.finished_at = datetime.now(timezone.utc)
        run.metrics = {"artifacts": artifact_count,"curated_records": curated_count,"quarantined_records": quarantined_count}
        self.db.commit()
