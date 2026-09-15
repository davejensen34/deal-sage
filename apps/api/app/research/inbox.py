"""Read-only case selection; pagination never requires candidate promotion."""

from sqlalchemy import func, or_, select

from app.domain.models import Business, CaseEvidence, EvidenceClaim, ResearchCase
from app.research.transitions import event_date_for, signal_type_for


def inbox_query(db, *, state=None, signal=None, since=None, until=None, date_basis="event"):
    stmt = select(ResearchCase)
    if state:
        # A geographic clue is a filter, not an identity resolution. Linked entity
        # geography and explicitly retained state assertions both remain useful.
        entity_ids = select(Business.id).where(func.upper(Business.state) == state)
        evidence_cases = select(CaseEvidence.case_id).where(
            func.upper(CaseEvidence.extracted_facts["state"].as_string()) == state
        )
        stmt = stmt.where(or_(ResearchCase.business_id.in_(entity_ids), ResearchCase.id.in_(evidence_cases)))
    if signal or since or until:
        pairs = db.execute(select(EvidenceClaim.case_id, EvidenceClaim.object_value, CaseEvidence.published_at).join(
            CaseEvidence, EvidenceClaim.evidence_id == CaseEvidence.id
        ).where(
            EvidenceClaim.case_id.in_(stmt.with_only_columns(ResearchCase.id)),
            EvidenceClaim.case_id == CaseEvidence.case_id,
            EvidenceClaim.predicate == "transition", EvidenceClaim.status == "asserted",
        )).yield_per(200)
        ids = set()
        for case_id, value, published_at in pairs:
            claim = EvidenceClaim(object_value=value)
            if signal and signal_type_for(claim) != signal:
                continue
            if since or until:
                # Legacy JSON dates need the same calendar validation as the brief.
                # Publication and retrieval dates must never stand in for events.
                try:
                    value = event_date_for(claim) if date_basis == "event" else (
                        published_at.date() if published_at else None
                    )
                except ValueError:
                    continue
                if value is None or (since and value < since) or (until and value > until):
                    continue
            ids.add(case_id)
        stmt = stmt.where(ResearchCase.id.in_(ids))
    return stmt
