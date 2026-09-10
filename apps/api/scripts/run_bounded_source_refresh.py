"""Run one explicitly approved source refresh against a local evidence corpus."""

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.research.landing import EvidenceLanding
from app.research.refresh import RefreshSource, SourceRefreshService
from app.research.sources.colorado import ColoradoBusinessEntitiesAdapter, parse_curated_record as parse_colorado
from app.research.sources.texas import TexasActiveFranchiseTaxpayersAdapter, parse_curated_record as parse_texas
from app.storage.local import LocalEvidenceStorage


SOURCES = {
    "colorado_business_entities": RefreshSource(ColoradoBusinessEntitiesAdapter(), parse_colorado, "colorado-entity-v1"),
    "texas_active_franchise_taxpayers": RefreshSource(TexasActiveFranchiseTaxpayersAdapter(), parse_texas, "texas-taxpayer-v1"),
}


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=SOURCES)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=25, choices=range(1, 101))
    args = parser.parse_args()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{args.database.resolve()}")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        refresh = await SourceRefreshService(
            db, EvidenceLanding(db, LocalEvidenceStorage(args.evidence_dir))
        ).run(
            SOURCES[args.source],
            record_limit=args.limit,
            approved_cost_usd=0,
            requested_by_user_id=None,
            requested_by_key="local-cli:bounded-refresh",
            requested_by_name="Local bounded refresh",
        )
        print(json.dumps({
            "id": refresh.id,
            "source_key": refresh.source_key,
            "status": refresh.status,
            "record_limit": refresh.record_limit,
            "actual_cost_usd": refresh.actual_cost_usd,
            "freshness_status": refresh.freshness_status,
            "result_summary": refresh.result_summary,
            "error_code": refresh.error_code,
        }, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
