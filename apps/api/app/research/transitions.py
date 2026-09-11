"""Interpret retained transition claims without rewriting evidence or deciding truth."""

from dataclasses import asdict
from datetime import date

from sqlalchemy import select

from app.domain.models import CaseEvidence, EvidenceClaim
from app.domain.transition_policies import POLICY_VERSION, transition_policy


EVENT_STATUSES = frozenset({"unknown", "planned", "reported", "completed", "cancelled"})


def signal_type_for(claim: EvidenceClaim) -> str:
    value = claim.object_value.get("signal_type")
    # Exact compatibility aliases from retained mortality packets. No keyword
    # guessing: an obituary can also report retirement, succession, or another person.
    if value is None and claim.object_value.get("event") in {"reported death", "reported_death"}:
        return "possible_death"
    return value if isinstance(value, str) else "unknown"


def event_date_for(claim: EvidenceClaim) -> date | None:
    value = claim.object_value.get("event_date")
    if value is None:
        return None
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError("Event date must be an ISO date or unknown")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("Event date must be an ISO date or unknown") from None


def validate_typed_transition(subject_type: str, value: dict) -> None:
    """Validate structure only; missing facts are allowed and remain unresolved."""
    policy = transition_policy(value["signal_type"])
    if subject_type != policy.subject_type:
        raise ValueError("Transition subject scope does not match its policy")
    status = value.get("event_status", "unknown")
    if not isinstance(status, str) or status not in EVENT_STATUSES:
        raise ValueError("Unsupported transition event status")
    for key in ("person", "business", "registration_number", "address"):
        if value.get(key) is not None and not isinstance(value[key], str):
            raise ValueError("Transition identity fields must be text or unknown")
    event_date_for(EvidenceClaim(object_value=value))


def transition_view(claim: EvidenceClaim, evidence: CaseEvidence) -> dict:
    signal_type = signal_type_for(claim)
    uncertainties = []
    try:
        policy = transition_policy(signal_type)
    except ValueError:
        policy = None
        uncertainties.append("No reviewed policy for this signal type; retain it for investigation.")
    try:
        event_date = event_date_for(claim)
    except ValueError:
        event_date = None
        uncertainties.append("The retained event date is malformed; review the source.")
    event_status = claim.object_value.get("event_status", "unknown")
    if not isinstance(event_status, str) or event_status not in EVENT_STATUSES:
        event_status = "unknown"
        uncertainties.append("The retained event status is unsupported.")
    if event_date is None:
        uncertainties.append("Event date is unknown; publication date is not a substitute.")
    if event_status != "completed":
        uncertainties.append("Event completion has not been established.")
    if policy and claim.subject_type != policy.subject_type:
        uncertainties.append("Subject scope needs review against the transition policy.")
    return {
        "claim_id": claim.id, "evidence_id": evidence.id,
        "signal_type": signal_type, "subject_type": claim.subject_type,
        "person": _text(claim.object_value.get("person")), "business": _text(claim.object_value.get("business")),
        "event_date": event_date, "event_status": event_status,
        "publication_date": evidence.published_at, "retrieved_at": evidence.retrieved_at,
        "publisher": evidence.publisher, "canonical_url": evidence.canonical_url,
        "classification": claim.classification, "claim_status": claim.status,
        "policy_version": POLICY_VERSION if policy else None,
        "policy": asdict(policy) if policy else None, "uncertainties": uncertainties,
    }


def _text(value) -> str | None:
    return value if isinstance(value, str) else None


def case_transitions(db, case_id: int) -> list[dict]:
    rows = db.execute(
        select(EvidenceClaim, CaseEvidence)
        .join(CaseEvidence, EvidenceClaim.evidence_id == CaseEvidence.id)
        .where(EvidenceClaim.case_id == case_id, CaseEvidence.case_id == case_id,
               EvidenceClaim.predicate == "transition")
        .order_by(EvidenceClaim.id)
    ).all()
    return [transition_view(claim, evidence) for claim, evidence in rows]
