from datetime import datetime, timezone
import json
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.domain.models import CuratedRecord, RawArtifact
from app.research.landing import EvidenceLanding, LandingEnvelope
from app.research.operational_corpus import replay_live_utah_delivery
from app.research.sources.utah import (
    REQUIRED_SHEETS,
    UTAH_BEL_DEFINITION,
    _empty_sheet,
    delivery_component_subject,
    parse_bel_package,
)
from app.storage.local import LocalEvidenceStorage


def test_replay_live_utah_delivery_excludes_fixtures_and_is_idempotent(tmp_path: Path):
    source_engine = create_engine("sqlite://")
    target_engine = create_engine("sqlite://")
    Base.metadata.create_all(source_engine)
    Base.metadata.create_all(target_engine)
    source_storage = LocalEvidenceStorage(tmp_path / "source")
    target_storage = LocalEvidenceStorage(tmp_path / "target")
    fixture = Path(__file__).parent / "fixtures/utah_bel_package.json"

    with Session(source_engine, expire_on_commit=False) as source_db:
        landing = EvidenceLanding(source_db, source_storage)
        run = landing.start_run(
            UTAH_BEL_DEFINITION.key,
            "Utah",
            "business_first",
            UTAH_BEL_DEFINITION.contract_fingerprint,
        )
        for sheet in REQUIRED_SHEETS:
            content = _empty_sheet(sheet)
            landing.land(
                run,
                _envelope(content, sheet=sheet),
                lambda value, name=sheet: delivery_component_subject(name, value),
                "utah-bel-delivery-component-v2",
                "curated-evidence-v1",
            )
        landing.land(
            run,
            _envelope(fixture.read_bytes()),
            parse_bel_package,
            "utah-bel-three-csv-v2",
            "curated-evidence-v1",
        )
        # A non-live contract fixture must never enter the operational corpus.
        fixture_run = landing.start_run(
            UTAH_BEL_DEFINITION.key,
            "Utah",
            "business_first",
            UTAH_BEL_DEFINITION.contract_fingerprint,
        )
        landing.land(
            fixture_run,
            _envelope(
                json.dumps(json.loads(fixture.read_text()), indent=2).encode(),
                live=False,
                record_id="contract-fixture",
            ),
            parse_bel_package,
            "contract-fixture-v1",
            "curated-evidence-v1",
        )

        with Session(target_engine, expire_on_commit=False) as target_db:
            first = replay_live_utah_delivery(
                source_db, source_storage, target_db, target_storage
            )
            second = replay_live_utah_delivery(
                source_db, source_storage, target_db, target_storage
            )

            assert first.artifacts == second.artifacts == 4
            assert first.quarantined_records == second.quarantined_records == 0
            assert target_db.scalar(select(func.count(RawArtifact.id))) == 4
            assert target_db.scalar(select(func.count(CuratedRecord.id))) == first.curated_records


def _envelope(
    content: bytes,
    *,
    sheet: str | None = None,
    live: bool = True,
    record_id: str = "approved-sample-package",
) -> LandingEnvelope:
    return LandingEnvelope(
        source_key=UTAH_BEL_DEFINITION.key,
        source_record_id=f"approved-sample-{sheet.lower()}" if sheet else record_id,
        canonical_url=UTAH_BEL_DEFINITION.landing_url,
        retrieved_at=datetime.now(timezone.utc),
        media_type="text/csv" if sheet else "application/json",
        contract_fingerprint=UTAH_BEL_DEFINITION.contract_fingerprint,
        request_metadata={"live_acquisition": live, **({"component": sheet} if sheet else {})},
        content=content,
    )
