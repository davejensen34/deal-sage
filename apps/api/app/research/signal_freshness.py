"""Evidence-cited intake routing, independent of ownership and confidence scores."""

from collections import Counter, defaultdict
from datetime import date, timedelta

from sqlalchemy import select

from app.domain.models import CaseEvidence, ClaimContradiction, EvidenceClaim, ResearchCase
from app.domain.transition_policies import transition_policy
from app.research.transitions import EVENT_STATUSES, event_date_for, signal_type_for

VERSION = "signal-intake-v1"
ELIGIBLE = frozenset({"recent_event", "recent_announcement", "planned_event"})


def iso_date(value):
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError("Signal dates must be ISO calendar dates")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("Signal dates must be ISO calendar dates") from None


def validate_policy(value: dict) -> dict:
    """Freeze an explicit assessment date; never age a run against today's clock."""
    if not isinstance(value, dict) or set(value) != {"version", "assessment_date", "lookback_days"}:
        raise ValueError("Signal intake requires version, assessment_date and lookback_days")
    days = value["lookback_days"]
    if value["version"] != VERSION or type(days) is not int or not 1 <= days <= 3650:
        raise ValueError("Unsupported signal intake version or lookback (1–3650 days)")
    as_of = iso_date(value["assessment_date"])
    try:
        as_of - timedelta(days=days + 1)
        as_of + timedelta(days=1)
    except OverflowError:
        raise ValueError("Signal assessment date cannot support its search window") from None
    return dict(value)


def dated_query(query: str, policy: dict | None) -> str:
    if policy is None:
        return query.strip()
    policy = validate_policy(policy)
    as_of = iso_date(policy["assessment_date"])
    # Search dates are discovery hints. They never establish event eligibility.
    after = as_of - timedelta(days=policy["lookback_days"] + 1)
    before = as_of + timedelta(days=1)
    return f"{query.strip()} after:{after.isoformat()} before:{before.isoformat()}"


def _supported(value, field, evidence):
    excerpt = value.get(f"{field}_excerpt")
    return (isinstance(excerpt, str) and bool(excerpt.strip())
            and excerpt in (evidence.relevant_excerpt or ""))


def assess_signal(claim: EvidenceClaim, evidence: CaseEvidence, policy: dict) -> dict:
    """Dates are cited assertions, not verified truth or a claim of ownership.

    A date-bearing excerpt must be retained with the claim. Normalization is an
    attributed claim-creation responsibility; substring support alone is not
    semantic verification. Publication metadata cannot substitute for that work.
    """
    policy = validate_policy(policy)
    as_of = iso_date(policy["assessment_date"])
    start = as_of - timedelta(days=policy["lookback_days"])
    value = claim.object_value
    dates = {}
    malformed_date = False
    for field in ("event_date", "announcement_date"):
        try:
            dates[field] = iso_date(value[field]).isoformat() if value.get(field) is not None else None
        except ValueError:
            # Audit snapshots must not echo arbitrary source text in date fields.
            dates[field] = None
            malformed_date = True
    status = value.get("event_status", "unknown")
    valid_status = isinstance(status, str) and status in EVENT_STATUSES
    row = {
        "claim_id": claim.id, "evidence_id": evidence.id,
        "event_date": dates["event_date"],
        "event_status": status if valid_status else "unknown",
        "announcement_date": dates["announcement_date"],
        "publication_date": evidence.published_at.isoformat() if evidence.published_at else None,
        "retrieved_at": evidence.retrieved_at.isoformat() if evidence.retrieved_at else None,
        "route": "date_verification", "reason": "no_supported_date", "eligible": False,
    }

    def route(name, reason):
        row.update(route=name, reason=reason, eligible=name in ELIGIBLE)
        return row

    if claim.status != "asserted" or not valid_status:
        return route("date_verification", "claim_or_status_needs_review")
    if malformed_date:
        return route("date_verification", "malformed_date")
    try:
        if transition_policy(signal_type_for(claim)).subject_type != claim.subject_type:
            return route("date_verification", "transition_subject_needs_review")
    except ValueError:
        return route("date_verification", "unsupported_transition_type")
    try:
        event = event_date_for(claim)
        announcement = iso_date(row["announcement_date"]) if row["announcement_date"] is not None else None
    except ValueError:
        return route("date_verification", "malformed_date")
    if event is not None and not _supported(value, "event_date", evidence):
        return route("date_verification", "event_date_needs_source_support")
    if announcement is not None and not _supported(value, "announcement_date", evidence):
        return route("date_verification", "announcement_date_needs_source_support")
    if announcement is not None and announcement > as_of:
        return route("date_verification", "announcement_after_assessment")
    if row["event_status"] == "cancelled":
        return route("background", "cancelled_event")
    if event is not None:
        if event < start:
            return route("background", "event_outside_lookback")
        if event > as_of:
            if row["event_status"] == "planned" and announcement and start <= announcement <= as_of:
                return route("planned_event", "recent_announcement_of_future_plan")
            return route("date_verification", "future_event_requires_recent_plan")
        if row["event_status"] == "planned":
            return route("date_verification", "planned_date_passed_completion_unknown")
        if row["event_status"] in {"completed", "reported"}:
            return route("recent_event", "reported_event_in_lookback")
        return route("date_verification", "event_status_unknown")
    if announcement and start <= announcement <= as_of:
        return route("recent_announcement", "recent_announcement_event_date_unknown")
    if announcement and announcement < start:
        return route("background", "announcement_outside_lookback")
    return route("date_verification", "no_supported_current_date")


def case_signal_intake(db, case_id: int, *, evidence_ids=None, claim_ids=None) -> dict | None:
    case = db.get(ResearchCase, case_id)
    if case is None:
        raise ValueError("Research case does not exist")
    if case.signal_intake_policy is None:
        return None
    policy = validate_policy(case.signal_intake_policy)
    pairs = db.execute(select(EvidenceClaim, CaseEvidence).join(
        CaseEvidence, EvidenceClaim.evidence_id == CaseEvidence.id
    ).where(EvidenceClaim.case_id == case_id, CaseEvidence.case_id == case_id,
            EvidenceClaim.predicate == "transition").order_by(EvidenceClaim.id)).all()
    conflicts = db.scalars(select(ClaimContradiction).where(
        ClaimContradiction.case_id == case_id, ClaimContradiction.status == "open"
    )).all()
    conflicted_ids = {cid for conflict in conflicts for cid in (conflict.left_claim_id, conflict.right_claim_id)}
    return assess_intake(pairs, policy, conflicted_ids=conflicted_ids,
                         evidence_ids=evidence_ids, claim_ids=claim_ids)


def assess_intake(pairs, policy, *, conflicted_ids=(), evidence_ids=None, claim_ids=None):
    """Shared pure routing for database cases and immutable evaluation snapshots."""
    policy = validate_policy(policy)
    rows = [assess_signal(claim, evidence, policy) for claim, evidence in pairs]
    groups = defaultdict(list)
    for index, (claim, _) in enumerate(pairs):
        value = claim.object_value
        # Conflicting assertions for the same named subject/type require review;
        # do not cherry-pick a recent date, including from outside the paid packet.
        subject = value.get("person") or value.get("business")
        if isinstance(subject, str) and subject.strip() and claim.status == "asserted":
            groups[(claim.subject_type, " ".join(subject.casefold().split()), signal_type_for(claim))].append(index)
    for indexes in groups.values():
        dates = {rows[i]["event_date"] for i in indexes if isinstance(rows[i]["event_date"], str)}
        statuses = {rows[i]["event_status"] for i in indexes if isinstance(rows[i]["event_status"], str)}
        if len(dates) > 1 or ("cancelled" in statuses and len(statuses) > 1):
            for i in indexes:
                rows[i].update(route="date_verification", reason="conflicting_event_dates", eligible=False)
    for row in rows:
        if row["claim_id"] in conflicted_ids:
            row.update(route="date_verification", reason="open_claim_conflict", eligible=False)
    if evidence_ids is not None:
        rows = [row for row in rows if row["evidence_id"] in evidence_ids]
    if claim_ids is not None:
        rows = [row for row in rows if row["claim_id"] in claim_ids]
    counts = dict(Counter(row["route"] for row in rows))
    return {"policy": policy, "signals": rows, "route_counts": counts,
            "eligible_signal_count": sum(row["eligible"] for row in rows),
            "analysis_allowed": any(row["eligible"] for row in rows)}


def require_recent_signal(db, case_id, *, evidence_ids=None, claim_ids=None):
    report = case_signal_intake(db, case_id, evidence_ids=evidence_ids, claim_ids=claim_ids)
    if report is not None and not report["analysis_allowed"]:
        raise ValueError("No eligible recent signal; retain background and verify dates before model analysis")
    return report
