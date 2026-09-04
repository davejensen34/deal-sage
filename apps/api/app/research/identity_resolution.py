import re
import unicodedata
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import (
    CaseAlias,
    CaseEvidence,
    ClaimContradiction,
    EvidenceClaim,
    EvidenceRelationship,
    IdentityResolution,
    ResearchCase,
)


DIRECTIONS = frozenset({"person_to_business", "business_to_person", "hybrid"})
ENTITY_TYPES = frozenset({"person", "business"})
CONTRADICTION_TYPES = frozenset(
    {"identity", "relationship", "timeline", "geography", "operating_status"}
)
EVIDENCE_RELATIONSHIPS = frozenset(
    {"duplicate", "syndicated", "same_publisher", "independent"}
)
NAME_DIMENSIONS = frozenset({"identity_name", "alias", "legal_name"})


class IdentityResolutionService:
    """Build reviewable hypotheses from multi-dimensional, case-local claims."""

    def __init__(self, db: Session):
        self.db = db

    def add_alias(
        self,
        case_id: int,
        *,
        entity_type: str,
        canonical_value: str,
        alias_value: str,
        source_claim_id: int,
    ) -> CaseAlias:
        self._require_case(case_id)
        claim = self._require_claim(case_id, source_claim_id)
        if entity_type not in ENTITY_TYPES or not canonical_value.strip() or not alias_value.strip():
            raise ValueError("Aliases require an entity type and non-empty values")
        alias = CaseAlias(
            case_id=case_id,
            entity_type=entity_type,
            canonical_value=canonical_value.strip(),
            alias_value=alias_value.strip(),
            normalized_value=normalize_identity(alias_value),
            source_claim_id=claim.id,
        )
        self.db.add(alias)
        self.db.commit()
        self.db.refresh(alias)
        return alias

    def record_contradiction(
        self,
        case_id: int,
        left_claim_id: int,
        right_claim_id: int,
        *,
        contradiction_type: str,
        rationale: str,
    ) -> ClaimContradiction:
        self._require_case(case_id)
        left = self._require_claim(case_id, left_claim_id)
        right = self._require_claim(case_id, right_claim_id)
        if left.id == right.id or contradiction_type not in CONTRADICTION_TYPES:
            raise ValueError("A contradiction requires two claims and a supported type")
        if not rationale.strip():
            raise ValueError("A contradiction requires an analyst-readable rationale")
        left_id, right_id = sorted((left.id, right.id))
        conflict = ClaimContradiction(
            case_id=case_id,
            left_claim_id=left_id,
            right_claim_id=right_id,
            contradiction_type=contradiction_type,
            rationale=rationale.strip(),
        )
        self.db.add(conflict)
        self.db.commit()
        self.db.refresh(conflict)
        return conflict

    def classify_evidence_pair(
        self, case_id: int, left_evidence_id: int, right_evidence_id: int
    ) -> EvidenceRelationship:
        self._require_case(case_id)
        left = self._require_evidence(case_id, left_evidence_id)
        right = self._require_evidence(case_id, right_evidence_id)
        if left.id == right.id:
            raise ValueError("Evidence independence requires two distinct items")
        relationship, basis = evidence_relationship(left, right)
        left_id, right_id = sorted((left.id, right.id))
        result = EvidenceRelationship(
            case_id=case_id,
            left_evidence_id=left_id,
            right_evidence_id=right_id,
            relationship_type=relationship,
            basis=basis,
        )
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def propose(
        self,
        case_id: int,
        *,
        direction: str,
        subject_value: str,
        candidate_value: str,
        supporting_claim_ids: list[int],
        contradictory_claim_ids: list[int] | None = None,
    ) -> IdentityResolution:
        self._require_case(case_id)
        if direction not in DIRECTIONS or not subject_value.strip() or not candidate_value.strip():
            raise ValueError("Identity resolution requires a direction and both identities")
        supporting = self._claims(case_id, supporting_claim_ids)
        contradictory = self._claims(case_id, contradictory_claim_ids or [])
        dimensions = sorted({_claim_dimension(claim) for claim in supporting})
        if not supporting or set(dimensions).issubset(NAME_DIMENSIONS):
            raise ValueError("Name-only identity resolution is not permitted")
        resolution = IdentityResolution(
            case_id=case_id,
            direction=direction,
            subject_value=subject_value.strip(),
            candidate_value=candidate_value.strip(),
            supporting_claim_ids=[claim.id for claim in supporting],
            contradictory_claim_ids=[claim.id for claim in contradictory],
            support_dimensions=dimensions,
        )
        self.db.add(resolution)
        self.db.commit()
        self.db.refresh(resolution)
        return resolution

    def _claims(self, case_id: int, claim_ids: list[int]) -> list[EvidenceClaim]:
        ids = list(dict.fromkeys(claim_ids))
        claims = self.db.scalars(select(EvidenceClaim).where(EvidenceClaim.id.in_(ids))).all()
        if len(claims) != len(ids) or any(claim.case_id != case_id for claim in claims):
            raise ValueError("Resolution claims must all belong to the same research case")
        by_id = {claim.id: claim for claim in claims}
        return [by_id[claim_id] for claim_id in ids]

    def _require_claim(self, case_id: int, claim_id: int) -> EvidenceClaim:
        return self._claims(case_id, [claim_id])[0]

    def _require_evidence(self, case_id: int, evidence_id: int) -> CaseEvidence:
        evidence = self.db.get(CaseEvidence, evidence_id)
        if evidence is None or evidence.case_id != case_id:
            raise ValueError("Evidence must belong to the same research case")
        return evidence

    def _require_case(self, case_id: int) -> ResearchCase:
        case = self.db.get(ResearchCase, case_id)
        if case is None:
            raise ValueError("Research case does not exist")
        return case


def normalize_identity(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    # Corporate abbreviations often vary only by internal punctuation (LLC vs
    # L.L.C.); remove that punctuation without joining ordinary words.
    ascii_value = re.sub(r"(?<=\w)[.'’](?=\w)", "", ascii_value)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", ascii_value.casefold()).split())


def evidence_relationship(
    left: CaseEvidence, right: CaseEvidence
) -> tuple[str, dict[str, Any]]:
    if left.content_hash == right.content_hash:
        return "duplicate", {"rule": "same_content_hash"}
    left_group = left.provenance.get("syndication_group") or left.provenance.get(
        "canonical_story_url"
    )
    right_group = right.provenance.get("syndication_group") or right.provenance.get(
        "canonical_story_url"
    )
    if left_group and left_group == right_group:
        return "syndicated", {"rule": "shared_syndication_provenance"}
    if normalize_identity(left.publisher) == normalize_identity(right.publisher):
        return "same_publisher", {"rule": "normalized_publisher_match"}
    return "independent", {"rule": "no_shared_provenance_observed"}


def _claim_dimension(claim: EvidenceClaim) -> str:
    if claim.predicate == "relationship":
        return "relationship"
    if claim.predicate in {"city", "state", "address", "geography"}:
        return "geography"
    if claim.predicate in {"date", "formation_date", "transition_date", "timeline"}:
        return "timeline"
    if claim.predicate in {"registration_number", "filing_identifier"}:
        return "registration"
    return claim.predicate
