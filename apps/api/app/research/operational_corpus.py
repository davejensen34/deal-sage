"""Assemble bounded state evidence without weakening its original provenance."""

from dataclasses import dataclass
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import RawArtifact
from app.research.landing import EvidenceLanding, LandingEnvelope
from app.research.sources.utah import (
    UTAH_BEL_DEFINITION,
    delivery_component_subject,
    parse_bel_package,
)
from app.storage.base import EvidenceStorage


@dataclass(frozen=True)
class ReplayResult:
    artifacts: int
    curated_records: int
    quarantined_records: int


def replay_live_utah_delivery(
    source_db: Session,
    source_storage: EvidenceStorage,
    target_db: Session,
    target_storage: EvidenceStorage,
) -> ReplayResult:
    """Replay only the approved live BEL artifacts, excluding contract fixtures."""
    artifacts = source_db.scalars(
        select(RawArtifact)
        .where(RawArtifact.source_key == UTAH_BEL_DEFINITION.key)
        .order_by(RawArtifact.id)
    ).all()
    live_artifacts = [
        artifact
        for artifact in artifacts
        if artifact.request_metadata.get("live_acquisition") is True
    ]
    if len(live_artifacts) != 4:
        raise ValueError("Expected the three approved Utah files and one joined package")

    verified = []
    for artifact in live_artifacts:
        content = source_storage.read(artifact.storage_key)
        if artifact.content_hash != sha256(content).hexdigest():
            raise ValueError("Retained Utah artifact no longer matches its content hash")
        verified.append((artifact, content))

    landing = EvidenceLanding(target_db, target_storage)
    run = landing.start_run(
        UTAH_BEL_DEFINITION.key,
        UTAH_BEL_DEFINITION.jurisdiction,
        "business_first",
        UTAH_BEL_DEFINITION.contract_fingerprint,
    )
    curated = 0
    quarantined = 0
    for artifact, content in verified:
        component = artifact.request_metadata.get("component")
        if component:
            parser = lambda value, sheet=component: delivery_component_subject(sheet, value)
            parser_version = "utah-bel-delivery-component-v2"
        elif artifact.media_type == "application/json":
            parser = parse_bel_package
            parser_version = "utah-bel-three-csv-v2"
        else:
            raise ValueError("Unexpected retained Utah artifact shape")
        outcomes = landing.land(
            run,
            LandingEnvelope(
                source_key=artifact.source_key,
                source_record_id=artifact.source_record_id,
                canonical_url=artifact.canonical_url,
                retrieved_at=artifact.retrieved_at,
                media_type=artifact.media_type,
                contract_fingerprint=artifact.contract_fingerprint,
                request_metadata={
                    **artifact.request_metadata,
                    "operational_replay": True,
                    "source_content_hash": artifact.content_hash,
                },
                content=content,
            ),
            parser,
            parser_version,
            "curated-evidence-v1",
        )
        curated += sum(outcome.status == "curated" for outcome in outcomes)
        quarantined += sum(outcome.status == "quarantined" for outcome in outcomes)
    return ReplayResult(len(live_artifacts), curated, quarantined)
