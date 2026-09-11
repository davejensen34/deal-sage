"""Offline evaluation of the real review bridge; no provider or live-store access."""

from collections import Counter
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

FROZEN_COHORT_SHA256 = "5a031b823aa84c022471c0b97929f47438c0c3227a31ab1ad65d1f62d1d6663f"

class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slot: str
    signal_type: str
    expected_promotion: bool
    outcome: Literal["promoted", "abstained", "failed"]
    publication_age_days: int | None = Field(default=None, ge=0)
    event_date_known: bool = False
    external_cost_cents: int | None = Field(default=None, ge=0)
    human_disposition: Literal["useful", "not_useful", "defer"] | None = None
    analyst_minutes: float | None = Field(default=None, ge=0, allow_inf_nan=False)


def ratio(numerator: int, denominator: int) -> dict:
    return {"numerator": numerator, "denominator": denominator,
            "value": numerator / denominator if denominator else None}


def summarize(observations: list[Observation]) -> dict:
    """Keep failures and missing measurements out of invented negative labels."""
    if len({row.slot for row in observations}) != len(observations):
        raise ValueError("Evaluation slots must be unique")
    completed = [r for r in observations if r.outcome != "failed"]
    promoted = [r for r in completed if r.outcome == "promoted"]
    positives = [r for r in completed if r.expected_promotion]
    true_positives = sum(r.expected_promotion for r in promoted)
    ages = [r.publication_age_days for r in observations if r.publication_age_days is not None]
    costs = [r.external_cost_cents for r in observations if r.external_cost_cents is not None]
    reviews = [r for r in observations if r.human_disposition is not None]
    minutes = [r.analyst_minutes for r in observations if r.analyst_minutes is not None]
    return {
        "slots": len(observations), "outcomes": dict(Counter(r.outcome for r in observations)),
        "completed": len(completed), "failed": len(observations) - len(completed),
        "promotion_precision": ratio(true_positives, len(promoted)),
        "positive_recall": ratio(true_positives, len(positives)),
        "fixture_agreement": ratio(sum((r.outcome == "promoted") == r.expected_promotion for r in completed), len(completed)),
        "promotion_coverage": ratio(len(promoted), len(observations)),
        "abstention": ratio(sum(r.outcome == "abstained" for r in observations), len(observations)),
        "event_date_coverage": ratio(sum(r.event_date_known for r in observations), len(observations)),
        "publication_age_days": {"measured": len(ages), "missing": len(observations)-len(ages), "mean": sum(ages)/len(ages) if ages else None},
        "external_cost_cents": {"measured": len(costs), "missing": len(observations)-len(costs), "known_total": sum(costs) if costs else None, "complete": len(costs)==len(observations) and bool(observations)},
        "human_dispositions": dict(Counter(r.human_disposition for r in reviews)),
        "human_review_coverage": ratio(len(reviews), len(observations)),
        "analyst_usefulness": ratio(sum(r.human_disposition == "useful" for r in reviews), len(reviews)),
        "analyst_minutes": {"measured": len(minutes), "total": sum(minutes) if minutes else None},
    }


def run_cohort(path: Path) -> dict:
    """Always create disposable in-memory stores; accept no runtime DB argument."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.database import Base
    from app.domain.models import ClaimContradiction
    from app.domain.transition_policies import transition_policy, POLICY_VERSION
    from app.research.cases import ResearchCaseService
    from app.research.model_proposals import ModelProposalService
    from app.research.proposal_dispositions import ModelProposalDispositionService
    from app.research.review_queue import ResearchReviewQueueService, ReviewQueueSpec

    raw = path.read_bytes()
    # Pin normalized JSON, not platform line endings. Changing cases or labels
    # requires a deliberate version/hash review rather than a silent easier cohort.
    fingerprint = sha256((json.dumps(json.loads(raw), indent=2) + "\n").encode()).hexdigest()
    if fingerprint != FROZEN_COHORT_SHA256:
        raise ValueError("Frozen cohort changed; review and version the protocol before running")
    manifest = json.loads(raw)
    if manifest.get("version") != "m7-transition-cohort-v1" or manifest.get("fictional") is not True:
        raise ValueError("Only the fictional version-one offline cohort is supported")
    cases = manifest["cases"]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Cohort requires nonempty unique slots")
    observations = []
    reasons = {}
    for fixture in cases:
        transition_policy(fixture["signal_type"])
        if type(fixture["expected_promotion"]) is not bool:
            raise ValueError("Pre-label must be boolean")
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with Session(engine, expire_on_commit=False) as db:
                service = ResearchCaseService(db)
                case = service.create_case(fixture["origin"])
                evidence = []
                for kind in ("owner", "transition"):
                    text = fixture[f"{kind}_excerpt"]
                    item = service.add_evidence(case.id, source_mode="case_specific_research",
                        canonical_url=f"https://example.test/{fixture['id']}/{kind}",
                        publisher="Fictional evaluation publisher", source_type="fictional_notice",
                        content=text.encode(), relevant_excerpt=text, extracted_facts={},
                        provenance={"fixture": fixture["id"]},
                        published_at=datetime.combine(date.fromisoformat(fixture["published_date"]), datetime.min.time(), tzinfo=timezone.utc))
                    evidence.append(item)
                owner = service.add_claim(case.id, evidence[0].id, subject_type="person_business_relationship",
                    predicate="relationship", object_value=fixture["owner"],
                    relationship_semantics=fixture["owner"]["role"], confidence=1,
                    classification="source_fact", source_authority="publisher", directness="direct")
                transition = service.add_claim(case.id, evidence[1].id, subject_type=fixture["subject_type"],
                    predicate="transition", object_value=fixture["transition"], confidence=1,
                    classification="source_fact", source_authority="publisher", directness="direct")
                proposal = ModelProposalService(db).record(case.id, task="match_analysis", provider="fixture",
                    model="no-model-called", prompt_version="fixture-v1", schema_version="fixture-v1",
                    execution_outcome="completed", proposed_output={"subject_name":fixture["owner"]["person"]},
                    supported_claim_ids=[owner.id, transition.id], supported_evidence_ids=[e.id for e in evidence])
                # Simulated acceptance tests the deterministic bridge. It is never
                # counted as a human usefulness observation or a model evaluation.
                ModelProposalDispositionService(db).add(proposal.id, analyst_name="Fictional fixture reviewer",
                    decision="accept", rationale="Simulated acceptance; deterministic validation must still apply.")
                if fixture["conflict"]:
                    db.add(ClaimContradiction(case_id=case.id,left_claim_id=owner.id,right_claim_id=transition.id,
                        contradiction_type="identity",rationale="Fictional conflicting identity evidence",status="open"))
                    db.commit()
                spec = ReviewQueueSpec(case.id, proposal.id, owner.id, transition.id,
                    fixture["owner"]["business"], fixture["owner"]["business"], fixture["state"], [])
                try:
                    ResearchReviewQueueService(db).promote(spec, analyst_name="Fictional fixture reviewer")
                    outcome = "promoted"
                except ValueError as error:
                    db.rollback()
                    outcome = "abstained"
                    reasons[fixture["id"]] = str(error)
                except Exception as error:
                    db.rollback()
                    outcome = "failed"
                    reasons[fixture["id"]] = type(error).__name__
        finally:
            engine.dispose()
        age = (date.fromisoformat(fixture["retrieved_date"]) - date.fromisoformat(fixture["published_date"])).days
        observations.append(Observation(slot=fixture["id"],signal_type=fixture["signal_type"],
            expected_promotion=fixture["expected_promotion"],outcome=outcome,
            publication_age_days=age,event_date_known=fixture["transition"]["event_date"] is not None,
            external_cost_cents=0))
    aggregate = summarize(observations)
    passed = aggregate["failed"] == 0 and aggregate["fixture_agreement"]["value"] == 1
    return {
        "version":"m7-transition-evaluation-v1", "policy_version":POLICY_VERSION,
        "cohort_sha256":fingerprint, "fictional":True,
        "target":manifest["evaluation_target"], "offline_contract_passed":passed,
        "live_precision_validated":False, "source_coverage_validated":False,
        "aggregate":aggregate,
        "by_signal":{family:summarize([r for r in observations if r.signal_type==family]) for family in sorted({r.signal_type for r in observations})},
        "observations":[r.model_dump() for r in observations], "abstention_or_failure_reasons":reasons,
        "limitations":["Pre-normalized fictional claims test the review bridge, not extraction or discovery.",
            "Promotion means eligibility for human review, not a verified opportunity.",
            "Publication ages are fixture dates, not measured live acquisition latency.",
            "Simulated acceptance is not observed analyst value; no human usefulness data was collected.",
            "No provider, live research corpus, search or model call was used."],
    }
