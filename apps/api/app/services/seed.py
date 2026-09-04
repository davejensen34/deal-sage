from datetime import date, datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.domain.models import (AuditEvent, Business, BusinessRelationship, CandidateMatch,
    Evidence, Person, ResearchStage, ResearchTrail, ReviewCase, Source, TargetProfile, TransitionSignal)
from app.domain.research import owner_readiness

CASES = [
 ("Alder Ridge Toolworks", "Eleanor", "Mae", "Voss", "Fort Collins", "CO", "validated", 93, 91, "owner", [], "Very strong match", ["owner_filing","exact_full_name","same_city","company_in_signal","independent_source","age_aligns","timeline_aligns"]),
 ("Northline Fabrication", "James", None, "Miller", "Columbus", "OH", "needs_review", 82, 39, "owner", ["Common name creates multiple plausible identities."], "Common-name collision", ["owner_filing","exact_full_name","common_name","insufficient_diversity"]),
 ("Copper Finch Design", "Marina", None, "Ortiz", "Phoenix", "AZ", "rejected", 22, 71, "registered_agent", ["Only registered-agent evidence exists; agency is not ownership."], "Registered-agent false positive", ["registered_agent_only","exact_full_name","same_city"]),
 ("Juniper Valley Foods", "Harold", "T", "Brenner", "Boise", "ID", "rejected", 38, 88, "former_owner", ["Ownership transferred four years before the signal."], "Former owner", ["former_owner","exact_full_name","same_city","age_aligns"]),
 ("Harborstone Marine", "Denise", None, "Calloway", "Norfolk", "VA", "rejected", 74, 31, "officer", ["Signal location is 1,300 miles from the business and person record."], "Geographic conflict", ["officer_filing","exact_full_name","geography_conflict"]),
 ("Prairie Lantern Supply", "Samuel", "Reed", "Hollis", "Wichita", "KS", "validated", 89, 84, "owner", [], "Strong indirect match", ["owner_filing","exact_full_name","same_city","occupation_aligns","relative_overlap","independent_source","timeline_aligns"]),
 ("Blue Heron Millwork", "Carol", None, "Webb", "Dover", "DE", "watchlist", 58, 44, "member", ["Only one ownership source and one brief memorial notice were found."], "Weak signal", ["exact_full_name","same_city","insufficient_diversity"]),
 ("Ember Peak Electric", "Ronald", "A", "Kim", "Reno", "NV", "rejected", 86, 24, "president", ["Published age conflicts with the business principal's birth year by 19 years."], "Conflicting age", ["owner_filing","exact_full_name","same_city","age_contradiction"]),
 ("Willow Bend Logistics", "Patricia", "June", "Sato", "Tacoma", "WA", "needs_review", 88, 76, "founder", ["The person is tied to three similarly named operating companies."], "Multiple businesses", ["owner_filing","exact_full_name","same_city","occupation_aligns","independent_source"]),
 ("Granite Orchard HVAC", "Victor", None, "Lang", "Manchester", "NH", "new", 78, 73, "managing_member", ["Current operating control has not been independently confirmed."], "Current control unclear", ["owner_filing","exact_full_name","same_city","timeline_aligns"]),
 ("Red Cedar Packaging", "Nadia", None, "Petrov", "Madison", "WI", "researching", 72, 66, "officer", ["Ownership filing is seven years old."], "Stale ownership source", ["exact_full_name","same_city","occupation_aligns","stale_source"]),
 ("Mosaic Field Services", "Thomas", "Lee", "Grant", "Austin", "TX", "validated", 91, 86, "owner", [], "Corroborated owner transition", ["owner_filing","exact_full_name","same_city","company_in_signal","independent_source","timeline_aligns"]),
 ("Silver Current Dental Lab", "Helen", None, "Brooks", "Portland", "ME", "watchlist", 65, 59, "partner", ["The memorial does not include occupation or company references."], "Limited signal detail", ["exact_full_name","same_city","owner_filing","insufficient_diversity"]),
 ("Canyon Thread Apparel", "Omar", None, "Rahman", "Albuquerque", "NM", "needs_review", 81, 69, "founder", ["A middle-name discrepancy remains unresolved."], "Alias requires review", ["owner_filing","same_city","occupation_aligns","independent_source"]),
 ("Lakeglass Printing", "Ruth", "E", "Dalton", "Duluth", "MN", "validated", 90, 89, "president", [], "Independent records align", ["owner_filing","exact_full_name","same_city","company_in_signal","independent_source","age_aligns"]),
 ("Sunward Irrigation", "Peter", None, "Cole", "Fresno", "CA", "new", 69, 63, "member", ["A second independent source is still needed."], "Single-source candidate", ["exact_full_name","same_city","owner_filing","insufficient_diversity"]),
 ("Ironleaf Safety", "Agnes", "Marie", "Dunn", "Pittsburgh", "PA", "researching", 84, 80, "owner", ["The latest annual filing has not yet been retrieved."], "Likely match under research", ["owner_filing","exact_full_name","same_city","relative_overlap","timeline_aligns"]),
 ("Tidemark Surveying", "George", None, "Price", "Savannah", "GA", "rejected", 61, 28, "officer", ["Two people share the name and professional license category."], "Identity collision", ["exact_full_name","common_name","geography_conflict","insufficient_diversity"]),
]


def seed_missing_research_trails(db: Session) -> None:
    """Backfill demo breadcrumbs when an older persisted demo database is reused."""
    profile = db.scalar(select(TargetProfile).limit(1))
    if not profile:
        profile = TargetProfile(name="Demo lower-middle-market businesses",criteria={"geography":"United States","employee_range":"11–50 (estimate)","status":"active"},provenance={"type":"fictional_demo","note":"Estimates are not registry facts."})
        db.add(profile); db.flush()
    for candidate in db.scalars(select(CandidateMatch)).all():
        if db.scalar(select(ResearchTrail.id).where(ResearchTrail.business_id == candidate.business_id)):
            continue
        relationship = candidate.relationship_record
        source = next((e.source for e in candidate.evidence if e.evidence_type == "business_filing"), None)
        trail = ResearchTrail(business_id=candidate.business_id,target_profile_id=profile.id,readiness_explanation="Evaluation pending")
        db.add(trail); db.flush()
        identity_ok, web_ok = candidate.owner_business_confidence >= 60, candidate.owner_business_confidence >= 70
        relationship_ok = candidate.owner_business_confidence >= 75 and relationship.relationship_type not in {"registered_agent","former_owner"}
        stages = [
            ResearchStage(trail_id=trail.id,stage_type="target_profile",sequence=1,status="validated",confidence=100,detail="Business matched the fictional demo target profile.",supporting_evidence=["Geography, active status, and estimated size align."]),
            ResearchStage(trail_id=trail.id,stage_type="business_discovered",sequence=2,status="validated",confidence=90,source_id=source.id if source else None,detail="Business was discovered in a fictional public directory."),
            ResearchStage(trail_id=trail.id,stage_type="entity_anchored",sequence=3,status="validated",confidence=96,source_id=source.id if source else None,detail="Authoritative fictional registry record anchors the legal entity."),
            ResearchStage(trail_id=trail.id,stage_type="business_identity_validated",sequence=4,status="validated" if identity_ok else "needs_review",confidence=candidate.owner_business_confidence,source_id=source.id if source else None,detail="Name, geography, and registration evidence were compared.",contradictions=[x.get("label","") for x in candidate.conflicting_signals],missing_evidence=[] if identity_ok else ["Independent business identifier"]),
            ResearchStage(trail_id=trail.id,stage_type="web_presence_validated",sequence=5,status="validated" if web_ok else "needs_review",confidence=max(candidate.owner_business_confidence-3,0),source_id=source.id if source else None,detail="Fictional company web presence was compared with the entity anchor.",supporting_evidence=["Name and geography align."] if web_ok else [],missing_evidence=[] if web_ok else ["Corroborating phone or address"]),
            ResearchStage(trail_id=trail.id,stage_type="person_discovered",sequence=6,status="validated",confidence=candidate.owner_business_confidence,person_id=candidate.person_id,source_id=source.id if source else None,detail=f"{candidate.person.full_name} was discovered with the filed role {relationship.relationship_type.replace('_',' ')}."),
            ResearchStage(trail_id=trail.id,stage_type="relationship_validated",sequence=7,status="validated" if relationship_ok else "insufficient_evidence",confidence=candidate.owner_business_confidence,person_id=candidate.person_id,relationship_id=relationship.id,source_id=source.id if source else None,detail="Person/business relationship retains the source role without upgrading it to ownership.",missing_evidence=[] if relationship_ok else ["Current controlling-owner evidence"]),
        ]
        db.add_all(stages); db.flush()
        ready, reason = owner_readiness(relationship, stages)
        trail.owner_research_ready, trail.readiness_explanation = ready, reason
        db.add(ResearchStage(trail_id=trail.id,stage_type="owner_research_ready",sequence=8,status="validated" if ready else "insufficient_evidence",confidence=candidate.owner_business_confidence,person_id=candidate.person_id,relationship_id=relationship.id,detail=reason))
    db.commit()


def seed_database(db: Session) -> None:
    if db.scalar(select(Business.id).limit(1)):
        seed_missing_research_trails(db)
        return
    now = datetime.now(timezone.utc)
    profile = TargetProfile(name="Demo lower-middle-market businesses", criteria={"geography":"United States","employee_range":"11–50 (estimate)","status":"active"}, provenance={"type":"fictional_demo","note":"Estimates are not registry facts."})
    db.add(profile); db.flush()
    for i, (company, first, middle, last, city, state, status, owner_score, signal_score, rel_type, conflicts, explanation, features) in enumerate(CASES, 1):
        business = Business(legal_name=company, doing_business_as=None, industry=["Manufacturing","Business Services","Construction","Distribution"][i%4], website=f"https://example.com/demo/{i}", address=f"{100+i} Market Street", city=city, state=state, postal_code=f"{80000+i}", jurisdiction=state, registration_number=f"DEMO-{state}-{1000+i}", formation_date=date(1994+i%20, 3, 1), employee_range="11–50 (estimate)", revenue_range="$2M–$10M (estimate)", ownership_type="privately held")
        person = Person(first_name=first, middle_name=middle, last_name=last, aliases=[], approximate_birth_year=1944+i%18, city=city, state=state)
        db.add_all([business, person]); db.flush()
        public = Source(source_type="business_registry", publisher=f"Fictional {state} Business Registry", canonical_url=f"https://example.com/demo/registry/{i}", published_at=now, jurisdiction=state, reliability="high", is_demo=True)
        notice = Source(source_type="memorial_notice", publisher="Fictional Community Memorial Archive", canonical_url=f"https://example.com/demo/memorial/{i}", published_at=now, jurisdiction=state, reliability="medium", is_demo=True)
        db.add_all([public, notice]); db.flush()
        relationship = BusinessRelationship(person_id=person.id, business_id=business.id, relationship_type=rel_type, start_date=date(2001+i%12,1,1), end_date=date(2020,1,1) if rel_type=="former_owner" else None, active=rel_type!="former_owner", confidence=owner_score/100, evidence_refs=[])
        signal = TransitionSignal(signal_type="possible_death" if i%6 else "succession", published_name=person.full_name, possible_transition_date=date(2025, (i%12)+1, min(i+3,28)), publication_date=date(2025,(i%12)+1,min(i+4,28)), city=city if "Geographic" not in explanation else "Miami", state=state if "Geographic" not in explanation else "FL", age=2025-(person.approximate_birth_year or 1950)+(19 if "age" in explanation.lower() else 0), relatives=[f"Alex {last}"], occupation_clues=[business.industry or "business"], business_clues=[company] if "indirect" not in explanation.lower() else [], source_id=notice.id, extraction_confidence=signal_score/100)
        db.add_all([relationship, signal]); db.flush()
        overall = min(owner_score, signal_score) + (5 if owner_score>=80 and signal_score>=80 else 0)
        candidate = CandidateMatch(person_id=person.id,business_id=business.id,relationship_id=relationship.id,signal_id=signal.id,owner_business_confidence=owner_score,signal_identity_confidence=signal_score,overall_candidate_confidence=min(overall,100),status=status,match_explanation=explanation,positive_signals=[{"label": f.replace("_"," ").title(), "impact": 10 if j else 25} for j,f in enumerate(features) if not f in {"common_name","geography_conflict","former_owner","registered_agent_only","age_contradiction","insufficient_diversity","stale_source"}],conflicting_signals=[{"label": c, "impact": -20} for c in conflicts],missing_evidence=[] if not conflicts else ["Independent current-control confirmation"],recommended_next_action="Confirm current ownership with a second independent public record." if conflicts else "Ready for analyst validation.",last_researched_at=now)
        db.add(candidate); db.flush()
        db.add_all([
            Evidence(candidate_id=candidate.id,evidence_type="business_filing",source_id=public.id,subject_type="business_relationship",subject_id=relationship.id,extracted_text=f"DEMO FACT: {person.full_name} is listed as {rel_type.replace('_',' ')} of {company}.",normalized_facts={"person":person.full_name,"business":company,"role":rel_type},extractor_type="seeded",evidence_strength="high" if owner_score>75 else "medium",explanation="Establishes the recorded business role; it does not independently prove current beneficial ownership.",classification="source_fact"),
            Evidence(candidate_id=candidate.id,evidence_type="transition_notice",source_id=notice.id,subject_type="transition_signal",subject_id=signal.id,extracted_text=f"DEMO FACT: A fictional public notice reports a transition signal for {person.full_name} of {city}, {state}.",normalized_facts={"name":person.full_name,"city":city,"state":state,"signal":"possible_death"},extractor_type="seeded",evidence_strength="high" if signal_score>75 else "low",explanation="Supports the transition signal but must be resolved to the business-associated identity.",classification="source_fact")])
        db.flush()
        trail = ResearchTrail(business_id=business.id,target_profile_id=profile.id,readiness_explanation="Evaluation pending")
        db.add(trail); db.flush()
        identity_ok = owner_score >= 60
        web_ok = owner_score >= 70
        relationship_ok = owner_score >= 75 and rel_type not in {"registered_agent", "former_owner"}
        stages = [
            ResearchStage(trail_id=trail.id,stage_type="target_profile",sequence=1,status="validated",confidence=100,detail="Business matched the fictional demo target profile.",supporting_evidence=["Geography, active status, and estimated size align."],missing_evidence=[]),
            ResearchStage(trail_id=trail.id,stage_type="business_discovered",sequence=2,status="validated",confidence=90,source_id=public.id,detail="Business was discovered in a fictional public directory.",supporting_evidence=[company]),
            ResearchStage(trail_id=trail.id,stage_type="entity_anchored",sequence=3,status="validated",confidence=96,source_id=public.id,detail="Authoritative fictional registry record anchors the legal entity.",supporting_evidence=[business.registration_number or "Registry identifier"]),
            ResearchStage(trail_id=trail.id,stage_type="business_identity_validated",sequence=4,status="validated" if identity_ok else "needs_review",confidence=owner_score,source_id=public.id,detail="Name, geography, and registration evidence were compared.",contradictions=conflicts,missing_evidence=[] if identity_ok else ["Independent business identifier"]),
            ResearchStage(trail_id=trail.id,stage_type="web_presence_validated",sequence=5,status="validated" if web_ok else "needs_review",confidence=max(owner_score-3,0),source_id=public.id,detail="Fictional company web presence was compared with the entity anchor.",supporting_evidence=["Name and geography align."] if web_ok else [],missing_evidence=[] if web_ok else ["Corroborating phone or address"]),
            ResearchStage(trail_id=trail.id,stage_type="person_discovered",sequence=6,status="validated",confidence=owner_score,person_id=person.id,source_id=public.id,detail=f"{person.full_name} was discovered with the filed role {rel_type.replace('_',' ')}."),
            ResearchStage(trail_id=trail.id,stage_type="relationship_validated",sequence=7,status="validated" if relationship_ok else "insufficient_evidence",confidence=owner_score,person_id=person.id,relationship_id=relationship.id,source_id=public.id,detail="Person/business relationship retains the source role without upgrading it to ownership.",contradictions=conflicts,missing_evidence=[] if relationship_ok else ["Current controlling-owner evidence"]),
        ]
        db.add_all(stages); db.flush()
        ready, reason = owner_readiness(relationship, stages)
        trail.owner_research_ready, trail.readiness_explanation = ready, reason
        db.add(ResearchStage(trail_id=trail.id,stage_type="owner_research_ready",sequence=8,status="validated" if ready else "insufficient_evidence",confidence=owner_score,person_id=person.id,relationship_id=relationship.id,detail=reason))
        db.add(ReviewCase(candidate_id=candidate.id, assigned_user="Morgan Lee", status="closed" if status in {"validated","rejected"} else "open", decision=status if status in {"validated","rejected"} else None, analyst_notes=[], decision_reason_codes=[]))
        db.add(AuditEvent(candidate_id=candidate.id,actor="DealSage demo seeder",action="candidate_created",after_state={"status":status},detail="Fictional demo candidate created."))
    db.commit()
