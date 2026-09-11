"""Prioritize untrusted discovery for investigation, never as proof of ownership."""
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.domain.models import (
    AuditEvent, CaseEvidence, ClaimContradiction, ResearchCase,
    ResearchFrontierItem, ResearchQuery, SourceCandidate, SourceCandidateDiscovery,
)

METHOD = "discovery-priority-v1"
QUESTIONS = {
    "obituary": ("verify_transition_identity", "Check the event date and person, then identify the named or unnamed business."),
    "funeral_home": ("verify_transition_identity", "Check the event date and person, then identify the named or unnamed business."),
    "newspaper": ("verify_transition_identity", "Check which person and event this report describes, including its date."),
    "probate_public_notice": ("verify_transition_identity", "Check the person, event date and any explicit business connection."),
    "business_website": ("resolve_business_identity", "Distinguish the local legal business from its brand; compare geography and registration."),
    "government": ("resolve_business_identity", "Compare legal name, registration and geography; preserve the exact reported role."),
    "licensing": ("resolve_business_identity", "Compare license holder, legal business and geography; a license is not ownership."),
}


def discovery_leads(db: Session, case_id: int) -> list[dict]:
    """Reproducible heuristic points, not calibrated probabilities or confidence.

    Repeated discovery never adds weight. Search-provider labels determine only
    what question to investigate. They cannot contribute to evidence confidence.
    """
    candidates = db.scalars(select(SourceCandidate).where(SourceCandidate.case_id == case_id)).all()
    queries = {q.id: q.query_text for q in db.scalars(select(ResearchQuery).where(ResearchQuery.case_id == case_id))}
    evidence = db.scalars(select(CaseEvidence).where(CaseEvidence.case_id == case_id)).all()
    discoveries = db.execute(select(SourceCandidateDiscovery.candidate_id, SourceCandidateDiscovery.query_id)
                             .join(SourceCandidate).where(SourceCandidate.case_id == case_id)).all()
    frontier = db.scalars(select(ResearchFrontierItem).where(ResearchFrontierItem.case_id == case_id)).all()
    conflicts = db.scalars(select(ClaimContradiction).where(
        ClaimContradiction.case_id == case_id, ClaimContradiction.status == "open")).all()
    rows = []
    for candidate in candidates:
        evidence_ids = sorted(e.id for e in evidence if e.provenance.get("candidate_id") == candidate.id
                              or e.canonical_url == candidate.canonical_url)
        question_type, question = QUESTIONS.get(candidate.likely_source_type, (
            "find_independent_evidence", "Use this clue to look for an independent source linking the person, business and location."))
        factors = [{"reason": "A retained discovery clue can guide investigation", "points": 20}]
        if candidate.likely_source_type in QUESTIONS:
            factors.append({"reason": "Provider-reported source type suggests a specific identity question; type is unverified", "points": 15})
        if evidence_ids:
            factors.append({"reason": "Retained evidence is available for comparison, not automatically accepted", "points": 10})
        if conflicts:
            factors.append({"reason": "Open case contradictions need comparison; this does not imply the lead resolves them", "points": 15})
        # Access affects the next permissible action, not the truth of the clue.
        action = "compare_evidence" if evidence_ids else "review_access"
        if candidate.access_decision == "blocked":
            action = "find_alternative"
            question_type = "find_independent_evidence"
            question = "Find an accessible independent source for this clue; do not retrieve the blocked source."
        elif not evidence_ids and candidate.access_decision == "approved":
            action = "retrieve_if_permitted"
        marker = f"Discovery lead #{candidate.id}: "
        queued = next((f for f in frontier if f.question.startswith(marker)), None)
        rows.append({
            "id": candidate.id, "url": candidate.canonical_url, "publisher": candidate.publisher or candidate.domain,
            "source_type": candidate.likely_source_type, "relevance": candidate.relevance_reason,
            "proposed_use": candidate.proposed_use, "provider": candidate.search_provider,
            "query_ids": sorted({qid for cid, qid in discoveries if cid == candidate.id}),
            "discovery_queries": [queries[qid] for qid in sorted({qid for cid, qid in discoveries if cid == candidate.id}) if qid in queries],
            "evidence_ids": evidence_ids, "access": candidate.access_decision,
            "access_reason": candidate.access_decision_reason,
            "priority": sum(f["points"] for f in factors), "method": METHOD, "factors": factors,
            "next_action": action, "question_type": question_type, "question": question,
            "frontier_id": queued.id if queued else None,
            "frontier_status": queued.status if queued else None,
        })
    return sorted(rows, key=lambda row: (-row["priority"], row["id"]))


def queue_lead(db: Session, case_id: int, candidate_id: int, *, user_id: int | None, actor: str) -> ResearchFrontierItem:
    """Snapshot a selected recommendation and attribution; never dispatch a tool.

    Stopped cases stay stopped. Repeated requests reuse the existing question,
    including completed/blocked questions, rather than resetting attempt budgets.
    """
    # A no-op update serializes competing selections on both SQLite and
    # PostgreSQL. Preserve timestamps and never reopen a stopped case.
    locked = db.execute(update(ResearchCase).where(
        ResearchCase.id == case_id, ResearchCase.status == "open"
    ).values(status=ResearchCase.status, updated_at=ResearchCase.updated_at))
    if locked.rowcount != 1:
        raise ValueError("Follow-up requires an open research case; stopped cases are not restarted")
    lead = next((r for r in discovery_leads(db, case_id) if r["id"] == candidate_id), None)
    if lead is None:
        raise ValueError("Discovery lead must belong to this research case")
    if lead["frontier_id"]:
        item = db.get(ResearchFrontierItem, lead["frontier_id"])
        db.commit()
        return item
    item = ResearchFrontierItem(
        case_id=case_id, question_type=lead["question_type"],
        question=f"Discovery lead #{candidate_id}: {lead['question']}",
        rationale=f"Untrusted discovery clue; {METHOD} priority {lead['priority']}. Next action: {lead['next_action']}. No fact acceptance or tool execution authorized.",
        priority=lead["priority"], supporting_claim_ids=[], max_attempts=2,
    )
    db.add(item)
    db.flush()
    db.add(AuditEvent(user_id=user_id, actor=actor, action="discovery_followup_queued",
                      detail="Analyst selected an untrusted clue for bounded follow-up; no external call.",
                      after_state={"case_id": case_id, "candidate_id": candidate_id,
                                   "frontier_id": item.id, "method": METHOD,
                                   "priority": lead["priority"], "factors": lead["factors"],
                                   "evidence_ids": lead["evidence_ids"], "query_ids": lead["query_ids"],
                                   "next_action": lead["next_action"]}))
    db.commit()
    db.refresh(item)
    return item
