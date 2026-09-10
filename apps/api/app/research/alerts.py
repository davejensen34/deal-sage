"""Deterministic in-app alerts derived only from completed refresh outcomes."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import AlertEvent, AlertSubscription, SourceRefresh


def evaluate_refresh_alerts(db: Session, refresh: SourceRefresh) -> list[AlertEvent]:
    """Emit subscribed failure/quarantine events; never initiate external work."""
    event_type = None
    if refresh.status == "failed":
        event_type = "refresh_failed"
    elif refresh.status == "partial" and refresh.result_summary.get("quarantined", 0) > 0:
        event_type = "quarantine_detected"
    if event_type is None:
        return []
    subscriptions = db.scalars(
        select(AlertSubscription).where(
            AlertSubscription.source_key == refresh.source_key,
            AlertSubscription.active.is_(True),
        )
    ).all()
    created = []
    for subscription in subscriptions:
        if event_type not in subscription.event_types:
            continue
        existing = db.scalar(select(AlertEvent.id).where(
            AlertEvent.subscription_id == subscription.id,
            AlertEvent.source_refresh_id == refresh.id,
            AlertEvent.event_type == event_type,
        ))
        if existing:
            continue
        count = refresh.result_summary.get("quarantined", 0)
        event = AlertEvent(
            subscription_id=subscription.id,
            source_refresh_id=refresh.id,
            event_type=event_type,
            title=f"{refresh.jurisdiction} refresh {'failed' if event_type == 'refresh_failed' else 'needs review'}",
            detail=(
                f"Safe failure code: {refresh.error_code or 'unknown'}. Previously landed evidence was unchanged."
                if event_type == "refresh_failed"
                else f"{count} curated outcome{'s' if count != 1 else ''} entered quarantine."
            ),
        )
        db.add(event)
        created.append(event)
    db.commit()
    return created
