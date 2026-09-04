from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import CuratedRecord, SignalResolution


STARTING_SUBJECT_TYPES = frozenset({"person", "transition_signal"})
TERMINAL_OUTCOMES = frozenset(
    {"business_resolved", "no_business_found", "relationship_unknown"}
)


class SignalResolutionService:
    """Apply deterministic lifecycle rules to signal-first research outcomes."""

    def __init__(self, db: Session):
        self.db = db

    def begin(self, starting_record_id: int) -> SignalResolution:
        starting_record = self.db.get(CuratedRecord, starting_record_id)
        if (
            starting_record is None
            or starting_record.status != "curated"
            or starting_record.subject_type not in STARTING_SUBJECT_TYPES
        ):
            raise ValueError("Resolution must begin from a curated person or transition signal")
        existing = self.db.scalar(
            select(SignalResolution).where(
                SignalResolution.starting_record_id == starting_record_id
            )
        )
        if existing is not None:
            return existing
        resolution = SignalResolution(starting_record_id=starting_record_id)
        self.db.add(resolution)
        self.db.commit()
        self.db.refresh(resolution)
        return resolution

    def finish(
        self,
        resolution_id: int,
        outcome: str,
        *,
        reason: str,
        resolved_by: str,
        business_record_id: int | None = None,
    ) -> SignalResolution:
        resolution = self.db.get(SignalResolution, resolution_id)
        if resolution is None:
            raise ValueError("Resolution does not exist")
        if resolution.outcome != "pending":
            raise ValueError("A terminal resolution cannot be changed")
        if outcome not in TERMINAL_OUTCOMES:
            raise ValueError("Unsupported resolution outcome")
        if not reason.strip() or not resolved_by.strip():
            raise ValueError("Terminal resolutions require a reason and actor")

        business_record = (
            self.db.get(CuratedRecord, business_record_id)
            if business_record_id is not None
            else None
        )
        requires_business = outcome in {"business_resolved", "relationship_unknown"}
        if requires_business and (
            business_record is None
            or business_record.status != "curated"
            or business_record.subject_type != "business"
        ):
            raise ValueError("This outcome requires an existing curated business record")
        if outcome == "no_business_found" and business_record_id is not None:
            raise ValueError("No-business-found cannot reference a business")

        resolution.outcome = outcome
        resolution.reason = reason.strip()
        resolution.resolved_by = resolved_by.strip()
        resolution.business_record_id = business_record_id
        resolution.resolved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(resolution)
        return resolution
