"""Refresh free state samples and replay the retained Utah BEL delivery."""

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.domain.models import CuratedRecord, RawArtifact
from app.research.ingestion import acquire_and_land_sample
from app.research.landing import EvidenceLanding
from app.research.operational_corpus import replay_live_utah_delivery
from app.research.sources.colorado import (
    ColoradoBusinessEntitiesAdapter,
    parse_curated_record as parse_colorado,
)
from app.research.sources.texas import (
    TexasActiveFranchiseTaxpayersAdapter,
    parse_curated_record as parse_texas,
)
from app.storage.local import LocalEvidenceStorage


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--utah-source-database", type=Path, required=True)
    parser.add_argument("--utah-source-evidence-dir", type=Path, required=True)
    parser.add_argument("--state-sample-size", type=int, default=25, choices=range(1, 101))
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


async def main() -> None:
    args = arguments()
    if not args.utah_source_database.is_file():
        raise SystemExit("Retained Utah source database was not found")
    args.database.parent.mkdir(parents=True, exist_ok=True)
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    target_engine = create_engine(f"sqlite:///{args.database.resolve()}")
    source_engine = create_engine(f"sqlite:///{args.utah_source_database.resolve()}")
    Base.metadata.create_all(target_engine)

    summaries: list[dict] = []
    with Session(target_engine, expire_on_commit=False) as target_db:
        landing = EvidenceLanding(target_db, LocalEvidenceStorage(args.evidence_dir))
        for adapter, parser, version in (
            (ColoradoBusinessEntitiesAdapter(), parse_colorado, "colorado-entity-v1"),
            (TexasActiveFranchiseTaxpayersAdapter(), parse_texas, "texas-taxpayer-v1"),
        ):
            result = await acquire_and_land_sample(
                adapter,
                landing,
                parser,
                limit=args.state_sample_size,
                parser_version=version,
                schema_version="curated-evidence-v1",
            )
            summaries.append({**result.public_summary(), "sample_kind": "live_bounded_refresh"})
        with Session(source_engine) as source_db:
            utah = replay_live_utah_delivery(
                source_db,
                LocalEvidenceStorage(args.utah_source_evidence_dir),
                target_db,
                LocalEvidenceStorage(args.evidence_dir),
            )
        summaries.append(
            {
                "source_key": "utah_business_entity_list",
                "jurisdiction": "Utah",
                "sample_kind": "retained_live_delivery_replay",
                "artifacts": utah.artifacts,
                "curated": utah.curated_records,
                "quarantined": utah.quarantined_records,
                "marginal_cost_usd": 0,
            }
        )
        aggregate = {
            "artifacts": target_db.scalar(select(func.count(RawArtifact.id))) or 0,
            "curated_records": target_db.scalar(select(func.count(CuratedRecord.id))) or 0,
            "quarantined_records": target_db.scalar(
                select(func.count(CuratedRecord.id)).where(CuratedRecord.status == "quarantined")
            )
            or 0,
        }

    payload = {
        "schema_version": "milestone-4-7-operational-corpus-v1",
        "contains_record_level_data": False,
        "sources": summaries,
        "aggregate": aggregate,
        "authorization": {
            "paid_search_calls": 0,
            "model_calls": 0,
            "note": "This corpus command does not invoke search or model providers.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
