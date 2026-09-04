"""Land bounded Milestone 3 source samples and publish aggregate-only results."""

import asyncio
import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.research.ingestion import acquire_and_land_sample
from app.research.landing import EvidenceLanding, LandingEnvelope
from app.research.sources.colorado import (
    ColoradoBusinessEntitiesAdapter,
    parse_curated_record as parse_colorado,
)
from app.research.sources.texas import (
    TexasActiveFranchiseTaxpayersAdapter,
    parse_curated_record as parse_texas,
)
from app.research.sources.utah import UTAH_BEL_DEFINITION, parse_bel_package
from app.storage.local import LocalEvidenceStorage


async def main() -> None:
    repository_root = Path(__file__).parents[3]
    private_root = repository_root / "data/research/milestone-3"
    result_path = (
        repository_root
        / "apps/api/app/research/results/milestone3_source_samples_summary.json"
    )
    private_root.mkdir(parents=True, exist_ok=True)
    result_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{private_root / 'samples.db'}")
    Base.metadata.create_all(engine)
    summaries = []
    with Session(engine, expire_on_commit=False) as db:
        landing = EvidenceLanding(db, LocalEvidenceStorage(private_root / "evidence"))
        for adapter, parser, parser_version in (
            (ColoradoBusinessEntitiesAdapter(), parse_colorado, "colorado-entity-v1"),
            (TexasActiveFranchiseTaxpayersAdapter(), parse_texas, "texas-taxpayer-v1"),
        ):
            result = await acquire_and_land_sample(
                adapter,
                landing,
                parser,
                limit=10,
                parser_version=parser_version,
                schema_version="curated-evidence-v1",
            )
            summaries.append(result.public_summary())

        # Utah's documented three-sheet example is a contract fixture, not a
        # live acquisition. It proves replayability without implying the $5
        # sample has been purchased or exercised.
        fixture_path = repository_root / "apps/api/tests/fixtures/utah_bel_package.json"
        content = fixture_path.read_bytes()
        run = landing.start_run(
            UTAH_BEL_DEFINITION.key,
            UTAH_BEL_DEFINITION.jurisdiction,
            "business_first",
            UTAH_BEL_DEFINITION.contract_fingerprint,
        )
        outcomes = landing.land(
            run,
            LandingEnvelope(
                source_key=UTAH_BEL_DEFINITION.key,
                source_record_id="official-layout-fictional-fixture-v1",
                canonical_url=UTAH_BEL_DEFINITION.landing_url,
                retrieved_at=run.started_at,
                media_type="application/json",
                contract_fingerprint=UTAH_BEL_DEFINITION.contract_fingerprint,
                request_metadata={"fixture": True, "live_acquisition": False, "cost_usd": 0},
                content=content,
            ),
            parse_bel_package,
            "utah-bel-three-sheet-v1",
            "curated-evidence-v1",
        )
        summaries.append(
            {
                "source_key": UTAH_BEL_DEFINITION.key,
                "jurisdiction": "Utah",
                "sample_kind": "fictional_contract_fixture",
                "live_source_exercised": False,
                "requested": 0,
                "retrieved": 0,
                "curated": sum(item.status == "curated" for item in outcomes),
                "quarantined": sum(item.status == "quarantined" for item in outcomes),
                "marginal_cost_usd": 0,
                "next_action": "Obtain explicit approval before purchasing the $5 live sample.",
            }
        )

    published = {
        "experiment": "Milestone 3 bounded multi-state source samples",
        "contains_record_level_data": False,
        "sources": summaries,
    }
    result_path.write_text(json.dumps(published, indent=2) + "\n")
    print(json.dumps(published, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
