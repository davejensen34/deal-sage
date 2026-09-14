"""Read-only business-first presentation of retained assertions, never a score."""

from sqlalchemy import select
from app.domain.models import EvidenceClaim

FIELDS = {
    "business_name": "Business", "legal_name": "Business", "business_clue": "Business",
    "location": "Location", "city": "City", "state": "State", "industry": "Industry",
    "business_activity": "Activity", "employee_count": "Employees",
    "revenue": "Revenue", "ebitda": "EBITDA", "company_type": "Company type",
}
RELEVANCE = {
    "possible_death": "The reported loss of a business-associated person may create a continuity or succession question.",
    "retirement": "Retirement may change who runs the business and how continuity is planned.",
    "succession": "A succession announcement can identify a change in responsibility and the people involved.",
    "ownership_change": "A reported ownership transfer can change control and the business's strategic direction.",
    "founder_exit": "A founder's departure may change leadership, relationships or operating continuity.",
    "dissolution": "A dissolution signal may affect business continuity and the status of its operations.",
    "restructuring": "Restructuring may change the business's organization or operating footprint.",
    "leadership_change": "A leadership change can identify new decision-makers or a shift in business direction.",
}


def lead_brief(db, case, evidence, transitions, intake, conflicts, frontier):
    facts = []
    sources = {source.id: source for source in evidence}

    def add(label, value, source, classification=None):
        if isinstance(value, bool) or not isinstance(value, (str, int, float)) or not str(value).strip():
            return
        row = {"label": label, "value": str(value).strip(), "evidence_id": source.id,
               "publisher": source.publisher, "url": source.canonical_url,
               "classification": classification or source.classification}
        if row not in facts:
            facts.append(row)

    for source in evidence:
        for field, label in FIELDS.items():
            add(label, source.extracted_facts.get(field), source)
    claims = db.scalars(select(EvidenceClaim).where(
        EvidenceClaim.case_id == case.id, EvidenceClaim.status == "asserted"
    ).order_by(EvidenceClaim.id)).all()
    for claim in claims:
        source = sources.get(claim.evidence_id)
        if source is not None:
            # These are explicit retained business labels, not resolved identity.
            add("Business", claim.object_value.get("business") or claim.object_value.get("business_name"), source, claim.classification)
    names = list(dict.fromkeys(f["value"] for f in facts if f["label"] == "Business"))
    title = names[0] if len(names) == 1 else ("Multiple business names reported" if names else "Business not yet identified")
    signal_rows = intake["signals"] if intake else []
    eligible_ids = {r["claim_id"] for r in signal_rows if r["eligible"]}
    asserted = [t for t in transitions if t["claim_status"] == "asserted"]
    ordered = sorted(asserted, key=lambda t: (t["claim_id"] not in eligible_ids, t["claim_id"]))
    signal = ordered[0] if ordered else None
    if eligible_ids:
        category = "recent"
    elif signal_rows and all(r["route"] == "background" for r in signal_rows):
        category = "background"
    else:
        category = "date_review"
    company_types = {f["value"].casefold().replace("_", " ") for f in facts if f["label"] == "Company type"}
    public = bool(company_types & {"public", "public company", "publicly traded"})
    private = bool(company_types & {"private", "private company", "privately held"})
    fit = "conflicting" if public and private else "public_company_reported" if public else "not_assessed"
    if public and len(names) > 1:
        fit = "conflicting"
    active_conflicts = [c.rationale for c in conflicts if c.status == "open"]
    why = RELEVANCE.get(signal["signal_type"], "A retained transition clue can guide further business research.") if signal else "Retained business information provides a starting point for transition research."
    if category == "background":
        why = "This historical transition provides background for comparing newer business developments."
    if fit == "public_company_reported":
        why += " The source reports a public company, outside the current private-company acquisition focus."
    pending = sorted((f for f in frontier if f.status == "pending"), key=lambda f: (-f.priority, f.id))
    signal_name = signal["signal_type"].replace("_", " ") if signal else "transition"
    if active_conflicts or len(names) > 1 or fit == "conflicting":
        gap = pending[0].question if pending else f"Resolve the conflicting business or transition assertions for {title}."
    elif category == "background":
        gap = f"Find a newer development for {title} before treating this {signal_name} as a current lead."
    elif category == "date_review":
        gap = f"Establish the event or announcement date for the reported {signal_name} at {title}."
    else:
        gap = pending[0].question if pending else f"Identify which business relationship the reported {signal_name} affects at {title}."
    return {"version": "business-brief-v1", "title": title, "reported_names": names,
            "category": category, "target_fit": fit, "signal": signal,
            "assessment_policy": intake["policy"] if intake else None,
            "timing": next((r for r in signal_rows if signal and r["claim_id"] == signal["claim_id"]), None),
            "facts": facts, "why_it_matters": why, "next_gap": gap,
            "conflicts": active_conflicts,
            "order": 2 if fit == "public_company_reported" else {"recent": 0, "date_review": 1, "background": 2}[category]}
