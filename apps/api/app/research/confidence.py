from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import (
    BusinessProfileObservation,
    CaseEvidence,
    ClaimContradiction,
    ConfidenceAssessment,
    EvidenceClaim,
    EvidenceRelationship,
    ResearchCase,
    ResearchInference,
)
from app.research.ingestion import assert_safe_source_content


METHOD_VERSION = "evidence-convergence-v1"
AUTHORITY = {"government": 1.0, "official": 1.0, "publisher": 0.8, "self_published": 0.65, "unknown": 0.4}
DIRECTNESS = {"direct_statement": 1.0, "direct": 1.0, "indirect": 0.6, "inferred": 0.4}
CLASSIFICATION = {"source_fact": 1.0, "third_party_estimate": 0.7}
PREDICATE_FACTORS = {
    "legal_name": ("business_identity", "legal_name", 30),
    "registration_number": ("business_identity", "registration_number", 45),
    "filing_identifier": ("business_identity", "filing_identifier", 45),
    "business_geography": ("business_identity", "geography", 20),
    "transition_name": ("transition_identity", "name", 45),
    "transition_date": ("transition_identity", "date", 25),
    "transition_geography": ("transition_identity", "geography", 15),
    "relative_overlap": ("transition_identity", "relative_overlap", 20),
    "recent_filing": ("operating_status", "recent_filing", 25),
    "business_website": ("operating_status", "business_website", 15),
}
RELATIONSHIP_IMPACTS = {
    "owner": 75, "co_owner": 70, "founder": 50, "operator": 40,
    "family_business_participant": 20, "executive": 15, "employee": 5,
    "former_owner": -50, "sold_business": -60, "retired": -40,
    "registered_agent": -35, "unknown": 0,
}
CONTRADICTION_AXES = {
    "identity": "business_identity", "relationship": "owner_relationship",
    "timeline": "transition_identity", "geography": "business_identity",
    "operating_status": "operating_status",
}
PROFILE_CLASSIFICATIONS = frozenset({"source_fact", "third_party_estimate", "dealsage_inference"})


class ConfidenceService:
    """Compute authoritative scores deterministically from persisted claims."""

    def __init__(self, db: Session):
        self.db = db

    def assess(self, case_id: int) -> ConfidenceAssessment:
        case = self._case(case_id)
        claims = self.db.scalars(
            select(EvidenceClaim).where(EvidenceClaim.case_id == case_id, EvidenceClaim.status == "asserted")
        ).all()
        evidence = {
            item.id: item
            for item in self.db.scalars(
                select(CaseEvidence).where(CaseEvidence.case_id == case_id)
            ).all()
        }
        groups = self._evidence_groups(case_id, [claim.evidence_id for claim in claims])
        factors: list[dict[str, Any]] = []
        seen: set[tuple[str, str, int]] = set()
        scores: dict[str, int] = defaultdict(int)
        for claim in claims:
            definition = self._factor_definition(claim)
            if definition is None:
                continue
            axis, feature, base = definition
            key = (axis, feature, groups[claim.evidence_id])
            if key in seen:
                factors.append(
                    {
                        "axis": axis,
                        "feature": feature,
                        "claim_id": claim.id,
                        "evidence_id": claim.evidence_id,
                        "evidence_group": groups[claim.evidence_id],
                        "impact": 0,
                        "suppressed_reason": "non_independent_evidence",
                    }
                )
                continue
            seen.add(key)
            multiplier = (
                claim.confidence
                * AUTHORITY.get(claim.source_authority, 0.4)
                * DIRECTNESS.get(claim.directness, 0.4)
                * CLASSIFICATION.get(claim.classification, 0.5)
                * _recency_multiplier(evidence[claim.evidence_id])
            )
            impact = round(base * multiplier)
            scores[axis] += impact
            factors.append({
                "axis": axis, "feature": feature, "claim_id": claim.id,
                "evidence_id": claim.evidence_id, "evidence_group": groups[claim.evidence_id],
                "base_impact": base, "multiplier": round(multiplier, 4),
                "recency_multiplier": _recency_multiplier(evidence[claim.evidence_id]),
                "impact": impact,
            })
        conflicts = self.db.scalars(
            select(ClaimContradiction).where(
                ClaimContradiction.case_id == case_id, ClaimContradiction.status == "open"
            )
        ).all()
        contradictory_ids: list[int] = []
        for conflict in conflicts:
            axis = CONTRADICTION_AXES[conflict.contradiction_type]
            scores[axis] -= 20
            contradictory_ids.extend((conflict.left_claim_id, conflict.right_claim_id))
            factors.append({
                "axis": axis, "feature": "open_contradiction", "contradiction_id": conflict.id,
                "claim_ids": [conflict.left_claim_id, conflict.right_claim_id], "impact": -20,
            })
        axes = {axis: max(0, min(100, scores[axis])) for axis in (
            "business_identity", "owner_relationship", "transition_identity", "operating_status"
        )}
        overall = min(axes["business_identity"], axes["owner_relationship"], axes["transition_identity"])
        status_values = {
            str(claim.object_value.get("value", "")).casefold()
            for claim in claims if claim.predicate == "operating_status"
        }
        if status_values & {"dissolved", "terminated", "inactive"}:
            overall = min(overall, 10)
        assessment = ConfidenceAssessment(
            case_id=case_id, method_version=METHOD_VERSION,
            business_identity=axes["business_identity"], owner_relationship=axes["owner_relationship"],
            transition_identity=axes["transition_identity"], operating_status=axes["operating_status"],
            overall_opportunity=overall, factors=factors,
            supporting_claim_ids=[factor["claim_id"] for factor in factors if "claim_id" in factor],
            contradictory_claim_ids=list(dict.fromkeys(contradictory_ids)),
        )
        self.db.add(assessment)
        case.confidence = {
            "method_version": METHOD_VERSION, **axes, "overall_opportunity": overall,
            "assessment_id": None,
        }
        self.db.flush()
        case.confidence = {**case.confidence, "assessment_id": assessment.id}
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def add_profile_observation(
        self, case_id: int, *, field_name: str, value: dict[str, Any],
        classification: str, confidence: float, supporting_claim_ids: list[int] | None = None,
        inference_id: int | None = None,
    ) -> BusinessProfileObservation:
        self._case(case_id)
        if classification not in PROFILE_CLASSIFICATIONS or not field_name.strip() or not 0 <= confidence <= 1:
            raise ValueError("Invalid business profile observation")
        assert_safe_source_content(value)
        claims = self._claims(case_id, supporting_claim_ids or [])
        inference = self.db.get(ResearchInference, inference_id) if inference_id else None
        if classification == "dealsage_inference":
            if inference is None or inference.case_id != case_id:
                raise ValueError("DealSage inference observations require a same-case inference")
        elif not claims or inference_id is not None:
            raise ValueError("Facts and estimates require supporting claims, not an inference")
        observation = BusinessProfileObservation(
            case_id=case_id, field_name=field_name.strip(), value=value,
            classification=classification, supporting_claim_ids=[claim.id for claim in claims],
            inference_id=inference_id, confidence=confidence,
        )
        self.db.add(observation)
        self.db.commit()
        self.db.refresh(observation)
        return observation

    def _factor_definition(self, claim: EvidenceClaim):
        if claim.predicate == "relationship":
            return ("owner_relationship", claim.relationship_semantics, RELATIONSHIP_IMPACTS[claim.relationship_semantics])
        if claim.predicate == "operating_status":
            value = str(claim.object_value.get("value", "")).casefold()
            return ("operating_status", value or "unknown", 60 if value == "active" else -70 if value in {"dissolved", "terminated"} else -60 if value == "inactive" else 0)
        return PREDICATE_FACTORS.get(claim.predicate)

    def _evidence_groups(self, case_id: int, evidence_ids: list[int]) -> dict[int, int]:
        parent = {evidence_id: evidence_id for evidence_id in evidence_ids}

        def root(value):
            while parent[value] != value:
                parent[value] = parent[parent[value]]
                value = parent[value]
            return value

        for relation in self.db.scalars(select(EvidenceRelationship).where(
            EvidenceRelationship.case_id == case_id,
            EvidenceRelationship.relationship_type.in_(("duplicate", "syndicated", "same_publisher")),
        )).all():
            if relation.left_evidence_id in parent and relation.right_evidence_id in parent:
                left, right = root(relation.left_evidence_id), root(relation.right_evidence_id)
                parent[max(left, right)] = min(left, right)
        return {evidence_id: root(evidence_id) for evidence_id in parent}

    def _claims(self, case_id: int, ids: list[int]) -> list[EvidenceClaim]:
        unique = list(dict.fromkeys(ids))
        claims = self.db.scalars(select(EvidenceClaim).where(EvidenceClaim.id.in_(unique))).all()
        if len(claims) != len(unique) or any(claim.case_id != case_id for claim in claims):
            raise ValueError("Profile claims must belong to the same research case")
        by_id = {claim.id: claim for claim in claims}
        return [by_id[value] for value in unique]

    def _case(self, case_id: int) -> ResearchCase:
        case = self.db.get(ResearchCase, case_id)
        if case is None:
            raise ValueError("Research case does not exist")
        return case


def _recency_multiplier(evidence: CaseEvidence) -> float:
    observed = evidence.published_at or evidence.retrieved_at
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    age_days = max(0, (datetime.now(timezone.utc) - observed).days)
    if age_days > 5 * 365:
        return 0.7
    if age_days > 2 * 365:
        return 0.85
    return 1.0
