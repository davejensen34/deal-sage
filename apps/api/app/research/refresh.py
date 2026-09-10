"""Explicit, bounded refresh orchestration over the existing evidence landing path."""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import AcquisitionRun, SourceRefresh
from app.research.ingestion import acquire_and_land_sample
from app.research.alerts import evaluate_refresh_alerts
from app.research.landing import EvidenceLanding, Parser
from app.research.sources.base import SourceAdapter


@dataclass(frozen=True)
class RefreshSource:
    adapter: SourceAdapter
    parser: Parser
    parser_version: str


class SourceRefreshService:
    """Run one approved source synchronously; scheduling remains out of scope."""

    def __init__(self, db: Session, landing: EvidenceLanding):
        self.db = db
        self.landing = landing

    async def run(
        self,
        source: RefreshSource,
        *,
        record_limit: int,
        approved_cost_usd: float,
        requested_by_user_id: int | None,
        requested_by_key: str,
        requested_by_name: str,
    ) -> SourceRefresh:
        if not 1 <= record_limit <= 100:
            raise ValueError("Refresh limit must be between 1 and 100 records")
        expected_cost = 0.0
        if expected_cost > approved_cost_usd:
            raise ValueError("Refresh exceeds its approved cost ceiling")
        running = self.db.scalar(
            select(SourceRefresh.id).where(
                SourceRefresh.source_key == source.adapter.definition.key,
                SourceRefresh.status == "running",
            )
        )
        if running:
            raise ValueError("A refresh for this source is already running")
        refresh = SourceRefresh(
            source_key=source.adapter.definition.key,
            jurisdiction=source.adapter.definition.jurisdiction,
            requested_by_user_id=requested_by_user_id,
            requested_by_key=requested_by_key,
            requested_by_name=requested_by_name,
            status="running",
            record_limit=record_limit,
            approved_cost_usd=approved_cost_usd,
            actual_cost_usd=0,
            contract_fingerprint=source.adapter.definition.contract_fingerprint,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(refresh)
        self.db.commit()
        self.db.refresh(refresh)
        try:
            result = await acquire_and_land_sample(
                source.adapter,
                self.landing,
                source.parser,
                limit=record_limit,
                parser_version=source.parser_version,
                schema_version="curated-evidence-v1",
                marginal_cost_usd=expected_cost,
            )
            acquisition = self.db.scalar(
                select(AcquisitionRun)
                .where(AcquisitionRun.source_key == refresh.source_key)
                .order_by(AcquisitionRun.id.desc())
            )
            summary = result.public_summary()
            freshness = summary["freshness"]
            refresh.status = "partial" if result.quarantined else "succeeded"
            refresh.acquisition_run_id = acquisition.id if acquisition else None
            refresh.actual_cost_usd = result.marginal_cost_usd
            refresh.freshness_status = freshness["status"]
            refresh.freshness_reason = freshness["reason"]
            refresh.result_summary = summary
        except Exception as error:
            # Provider bodies can contain unsafe or sensitive content. Persist only
            # the exception class as an operational failure code.
            refresh.status = "failed"
            refresh.error_code = type(error).__name__
            refresh.freshness_status = "refresh_failed"
            refresh.freshness_reason = "The latest attempt failed; previously landed evidence was not changed."
        refresh.finished_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(refresh)
        evaluate_refresh_alerts(self.db, refresh)
        return refresh
