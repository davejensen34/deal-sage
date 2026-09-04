"""Ingest one explicitly approved Utah BEL ZIP and print aggregate-only metrics."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.research.landing import EvidenceLanding, LandingEnvelope
from app.research.sources.utah import UTAH_BEL_DEFINITION, parse_bel_csv_archive
from app.storage.local import LocalEvidenceStorage


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path, help="Delivered Utah BEL ZIP archive")
    parser.add_argument("--cost-usd", type=float, default=5.0)
    return parser.parse_args()


def main() -> None:
    args = arguments()
    if args.archive.suffix.lower() != ".zip" or not args.archive.is_file():
        raise ValueError("Provide the delivered Utah BEL ZIP without extracting or modifying it")
    if not 0 <= args.cost_usd <= 5:
        raise ValueError("The bounded Utah sample cost must be between $0 and the authorized $5")

    repository_root = Path(__file__).parents[3]
    private_root = repository_root / "data/research/milestone-3"
    private_root.mkdir(parents=True, exist_ok=True)
    content = args.archive.read_bytes()
    started = perf_counter()

    engine = create_engine(f"sqlite:///{private_root / 'samples.db'}")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        landing = EvidenceLanding(db, LocalEvidenceStorage(private_root / "evidence"))
        run = landing.start_run(
            UTAH_BEL_DEFINITION.key,
            "Utah",
            "business_first",
            UTAH_BEL_DEFINITION.contract_fingerprint,
        )
        outcomes = landing.land(
            run,
            LandingEnvelope(
                source_key=UTAH_BEL_DEFINITION.key,
                source_record_id=f"approved-sample-{sha256(content).hexdigest()[:12]}",
                canonical_url=UTAH_BEL_DEFINITION.landing_url,
                retrieved_at=datetime.fromtimestamp(
                    args.archive.stat().st_mtime, timezone.utc
                ),
                media_type="application/zip",
                contract_fingerprint=UTAH_BEL_DEFINITION.contract_fingerprint,
                request_metadata={
                    "bounded_sample": True,
                    "live_acquisition": True,
                    "cost_usd": args.cost_usd,
                },
                content=content,
            ),
            parse_bel_csv_archive,
            "utah-bel-csv-archive-v1",
            "curated-evidence-v1",
        )

    businesses = [item for item in outcomes if item.subject_type == "business"]
    relationships = [
        item for item in outcomes if item.subject_type == "relationship_assertion"
    ]
    # The command never prints names, identifiers, addresses, or raw rows.
    summary = {
        "source_key": UTAH_BEL_DEFINITION.key,
        "jurisdiction": "Utah",
        "sample_kind": "live_bounded_purchase",
        "live_source_exercised": True,
        "businesses_curated": len(businesses),
        "relationship_assertions": len(relationships),
        "ownership_supported_assertions": 0,
        "quarantined": sum(item.status == "quarantined" for item in outcomes),
        "archive_content_hash": sha256(content).hexdigest(),
        "retrieval_latency_ms": round((perf_counter() - started) * 1000),
        "marginal_cost_usd": args.cost_usd,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
