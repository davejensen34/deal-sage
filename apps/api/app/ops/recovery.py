"""Verify that durable database evidence references resolve to immutable bytes.

Backup orchestration deliberately lives outside the application process. This
module supplies the portable integrity contract used after restoring into a
separate database and evidence root.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.domain.models import RawArtifact


@dataclass(frozen=True)
class RecoveryVerification:
    schema_revision: str
    expected_schema_revision: str | None
    artifact_count: int
    artifact_bytes: int
    missing_keys: tuple[str, ...]
    size_mismatches: tuple[str, ...]
    hash_mismatches: tuple[str, ...]

    @property
    def valid(self) -> bool:
        schema_matches = self.expected_schema_revision in (None, self.schema_revision)
        return schema_matches and not (self.missing_keys or self.size_mismatches or self.hash_mismatches)

    def as_dict(self) -> dict[str, object]:
        return {**asdict(self), "valid": self.valid}


def verify_restored_evidence(
    db: Session, evidence_root: Path, expected_schema_revision: str | None = None
) -> RecoveryVerification:
    """Check restored artifact bytes against authoritative database metadata."""
    revision = db.execute(text("select version_num from alembic_version")).scalar_one()
    root = evidence_root.resolve()
    missing: list[str] = []
    wrong_size: list[str] = []
    wrong_hash: list[str] = []
    total_bytes = 0
    artifacts = db.scalars(select(RawArtifact).order_by(RawArtifact.id)).all()
    for artifact in artifacts:
        path = (root / artifact.storage_key).resolve()
        if root not in path.parents or not path.is_file():
            missing.append(artifact.storage_key)
            continue
        content = path.read_bytes()
        total_bytes += len(content)
        if len(content) != artifact.byte_size:
            wrong_size.append(artifact.storage_key)
        if sha256(content).hexdigest() != artifact.content_hash:
            wrong_hash.append(artifact.storage_key)
    return RecoveryVerification(
        schema_revision=revision,
        expected_schema_revision=expected_schema_revision,
        artifact_count=len(artifacts),
        artifact_bytes=total_bytes,
        missing_keys=tuple(missing),
        size_mismatches=tuple(wrong_size),
        hash_mismatches=tuple(wrong_hash),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a separately restored DealSage dataset")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--expected-schema-revision")
    args = parser.parse_args()
    with Session(create_engine(args.database_url)) as db:
        result = verify_restored_evidence(db, args.evidence_root, args.expected_schema_revision)
    print(json.dumps(result.as_dict(), indent=2))
    if not result.valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
