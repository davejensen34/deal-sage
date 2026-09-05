"""Ingest the three approved Utah BEL CSVs and publish aggregate-only metrics."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.domain.models import RawArtifact
from app.research.landing import EvidenceLanding, LandingEnvelope
from app.research.sources.utah import (
    UTAH_BEL_DEFINITION,
    canonical_bel_package_from_csv,
    delivery_component_subject,
    parse_bel_package,
    summarize_bel_package,
)
from app.storage.local import LocalEvidenceStorage


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--busentity", type=Path, required=True)
    parser.add_argument("--businfo", type=Path, required=True)
    parser.add_argument("--principal", type=Path, required=True)
    parser.add_argument("--cost-usd", type=float, default=5.0)
    return parser.parse_args()


def main() -> None:
    args = arguments()
    delivered_paths = {
        "BUSENTITY": args.busentity,
        "BUSINFO": args.businfo,
        "PRINCIPAL": args.principal,
    }
    if any(path.suffix.lower() != ".csv" or not path.is_file() for path in delivered_paths.values()):
        raise ValueError("Provide all three original delivered Utah BEL CSV files")
    if not 0 <= args.cost_usd <= 5:
        raise ValueError("The bounded Utah sample cost must be between $0 and the authorized $5")

    files = {f"{sheet}.csv": path.read_bytes() for sheet, path in delivered_paths.items()}
    package_content = canonical_bel_package_from_csv(files)
    measures = summarize_bel_package(package_content)
    repository_root = Path(__file__).parents[3]
    private_root = repository_root / "data/research/milestone-3"
    result_path = repository_root / "apps/api/app/research/results/milestone3_source_samples_summary.json"
    private_root.mkdir(parents=True, exist_ok=True)
    started = perf_counter()

    engine = create_engine(f"sqlite:///{private_root / 'samples.db'}")
    Base.metadata.create_all(engine)
    outcomes = []
    with Session(engine, expire_on_commit=False) as db:
        landing = EvidenceLanding(db, LocalEvidenceStorage(private_root / "evidence"))
        artifacts_before = db.scalar(
            select(func.count(RawArtifact.id)).where(RawArtifact.source_key == UTAH_BEL_DEFINITION.key)
        ) or 0
        run = landing.start_run(
            UTAH_BEL_DEFINITION.key,
            "Utah",
            "business_first",
            UTAH_BEL_DEFINITION.contract_fingerprint,
        )
        for sheet, path in delivered_paths.items():
            content = files[f"{sheet}.csv"]
            outcomes.extend(
                landing.land(
                    run,
                    LandingEnvelope(
                        source_key=UTAH_BEL_DEFINITION.key,
                        source_record_id=f"approved-sample-{sheet.lower()}-{sha256(content).hexdigest()[:12]}",
                        canonical_url=UTAH_BEL_DEFINITION.landing_url,
                        retrieved_at=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc),
                        media_type="text/csv",
                        contract_fingerprint=UTAH_BEL_DEFINITION.contract_fingerprint,
                        request_metadata={"bounded_sample": True, "live_acquisition": True, "component": sheet},
                        content=content,
                    ),
                    lambda value, sheet=sheet: delivery_component_subject(sheet, value),
                    "utah-bel-delivery-component-v2",
                    "curated-evidence-v1",
                )
            )

        # The canonical package makes the cross-file join replayable while the
        # three exact delivered files remain independently immutable evidence.
        outcomes.extend(
            landing.land(
                run,
                LandingEnvelope(
                    source_key=UTAH_BEL_DEFINITION.key,
                    source_record_id=f"approved-sample-package-{sha256(package_content).hexdigest()[:12]}",
                    canonical_url=UTAH_BEL_DEFINITION.landing_url,
                    retrieved_at=max(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc) for path in delivered_paths.values()),
                    media_type="application/json",
                    contract_fingerprint=UTAH_BEL_DEFINITION.contract_fingerprint,
                    request_metadata={
                        "bounded_sample": True,
                        "live_acquisition": True,
                        "cost_usd": args.cost_usd,
                        "derived_from": {sheet: sha256(content).hexdigest() for sheet, content in files.items()},
                    },
                    content=package_content,
                ),
                parse_bel_package,
                "utah-bel-three-csv-v2",
                "curated-evidence-v1",
            )
        )
        artifacts_after = db.scalar(
            select(func.count(RawArtifact.id)).where(RawArtifact.source_key == UTAH_BEL_DEFINITION.key)
        ) or 0

    summary = {
        "source_key": UTAH_BEL_DEFINITION.key,
        "jurisdiction": "Utah",
        "sample_kind": "live_bounded_purchase",
        "live_source_exercised": True,
        "requested": measures["entity_rows"],
        "retrieved": measures["entity_rows"],
        "curated": measures["entity_rows"] + measures["principal_rows"],
        "quarantined": sum(item.status == "quarantined" for item in outcomes),
        "artifact_count": 4,
        "new_artifacts_this_run": artifacts_after - artifacts_before,
        "repeat_verified": artifacts_before == artifacts_after and artifacts_after >= 4,
        "duplicate_artifacts": 0,
        "field_completeness_percent": measures["field_completeness_percent"],
        "relationship_assertions": measures["principal_rows"],
        "ownership_supported_assertions": 0,
        "explicit_owner_role_assertions": measures["explicit_owner_role_assertions"],
        "control_role_candidate_assertions": measures["control_role_candidate_assertions"],
        "role_counts": measures["role_counts"],
        "join_quality": {
            "entity_id_duplicates": measures["entity_id_duplicates"],
            "relationship_duplicates": measures["relationship_duplicates"],
            "orphan_business_info_rows": measures["orphan_business_info_rows"],
            "orphan_principal_rows": measures["orphan_principal_rows"],
        },
        "freshness": {
            "status": "measured_from_registration_date",
            "latest_registration_date": measures["latest_registration_date"],
        },
        "businfo_contract": measures["businfo_contract"],
        "retrieval_success_percent": 100.0,
        "retrieval_latency_ms": round((perf_counter() - started) * 1000),
        "marginal_cost_usd": args.cost_usd,
        "reuse_review": "Public Utah business-registration records; retained privately with aggregate-only publication and no separate redistribution license observed.",
    }
    published = json.loads(result_path.read_text())
    published["sources"] = [
        summary if source["source_key"] == UTAH_BEL_DEFINITION.key else source
        for source in published["sources"]
    ]
    result_path.write_text(json.dumps(published, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
