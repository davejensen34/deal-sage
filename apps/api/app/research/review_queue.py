"""Bridge an analyst-accepted research proposal into the downstream review queue."""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import (
    AuditEvent,
    Business,
    BusinessRelationship,
    CandidateMatch,
    CaseEvidence,
    Evidence,
    EvidenceClaim,
    ModelProposal,
    ModelProposalDisposition,
    Person,
    ResearchCase,
    ReviewCase,
    Source,
    TransitionSignal,
)
from app.services.candidate_scoring import record_score_assessment


AUTHORITY_MULTIPLIERS = {
    "government": 1.0,
    "official": 1.0,
    "publisher": 0.8,
    "funeral_home_obituary": 0.8,
    "self_published": 0.65,
    "first_party_business": 0.65,
}
DIRECTNESS_MULTIPLIERS = {"direct": 1.0, "direct_statement": 1.0, "document_context": 0.8}


@dataclass(frozen=True)
class ReviewQueueSpec:
    case_id: int
    accepted_proposal_id: int
    owner_claim_id: int
    transition_claim_id: int
    business_label: str
    doing_business_as: str
    state: str
    missing_evidence: list[str]


class ResearchReviewQueueService:
    """Create a conservative review object without treating model output as fact."""

    def __init__(self, db: Session):
        self.db = db

    def promote(self, spec: ReviewQueueSpec, *, analyst_name: str) -> CandidateMatch:
        case = self.db.get(ResearchCase, spec.case_id)
        proposal = self.db.get(ModelProposal, spec.accepted_proposal_id)
        if case is None or proposal is None or proposal.case_id != case.id:
            raise ValueError("Queue promotion requires a same-case proposal")
        accepted = self.db.scalar(
            select(ModelProposalDisposition).where(
                ModelProposalDisposition.proposal_id == proposal.id,
                ModelProposalDisposition.decision == "accept",
            )
        )
        if accepted is None or proposal.execution_outcome != "completed":
            raise ValueError("Queue promotion requires an accepted completed proposal")
        if case.candidate_match_id:
            return self.db.get(CandidateMatch, case.candidate_match_id)

        owner_claim = self._claim(case.id, spec.owner_claim_id)
        transition_claim = self._claim(case.id, spec.transition_claim_id)
        subject_name = str(proposal.proposed_output.get("subject_name", "")).strip()
        if not self._claim_names(owner_claim, subject_name) or not self._claim_names(transition_claim, subject_name):
            raise ValueError("Queue proposal and source claims must identify the same person")
        if owner_claim.relationship_semantics not in {"owner", "co_owner"}:
            raise ValueError("Queue promotion requires explicit owner-role source evidence")

        first_name, last_name = _split_person_name(subject_name)
        person = Person(first_name=first_name, last_name=last_name, aliases=[], state=spec.state)
        business = Business(
            legal_name=spec.business_label,
            doing_business_as=spec.doing_business_as,
            status="unknown",
            state=spec.state,
            jurisdiction=spec.state,
            ownership_type="privately held; source-reported franchise ownership",
        )
        self.db.add_all([person, business])
        self.db.flush()

        relationship = BusinessRelationship(
            person_id=person.id,
            business_id=business.id,
            relationship_type="former_owner",
            active=False,
            confidence=_claim_score(owner_claim, 75) / 100,
            evidence_refs=[owner_claim.evidence_id],
        )
        signal_source = self._source_for_evidence(self.db.get(CaseEvidence, transition_claim.evidence_id), spec.state)
        signal = TransitionSignal(
            signal_type="possible_death",
            published_name=subject_name,
            state=spec.state,
            business_clues=[spec.doing_business_as],
            source_id=signal_source.id,
            extraction_confidence=_claim_score(transition_claim, 45) / 100,
        )
        self.db.add_all([relationship, signal])
        self.db.flush()

        owner_score = _claim_score(owner_claim, 75)
        signal_score = _claim_score(transition_claim, 45)
        candidate = CandidateMatch(
            person_id=person.id,
            business_id=business.id,
            relationship_id=relationship.id,
            signal_id=signal.id,
            owner_business_confidence=owner_score,
            signal_identity_confidence=signal_score,
            overall_candidate_confidence=min(owner_score, signal_score),
            status="needs_review",
            match_explanation=(
                "An analyst accepted explicit source-reported ownership at the transition. "
                "The local legal entity, successor, and current operating status remain unresolved."
            ),
            positive_signals=[
                {"label": "Explicit owner statement", "impact": owner_score},
                {"label": "Transition subject identified", "impact": signal_score},
            ],
            conflicting_signals=[],
            missing_evidence=spec.missing_evidence,
            recommended_next_action="Resolve the Utah legal entity, successor, and current local operating status.",
            last_researched_at=datetime.now(timezone.utc),
        )
        self.db.add(candidate)
        self.db.flush()
        copied_evidence = []
        for evidence in self.db.scalars(
            select(CaseEvidence).where(CaseEvidence.case_id == case.id).order_by(CaseEvidence.id)
        ).all():
            source = signal_source if evidence.id == transition_claim.evidence_id else self._source_for_evidence(evidence, spec.state)
            copied = Evidence(
                    candidate_id=candidate.id,
                    evidence_type=evidence.source_type,
                    source_id=source.id,
                    subject_type="research_case",
                    subject_id=case.id,
                    extracted_text=evidence.relevant_excerpt or "Qualified source retained without a selected excerpt.",
                    normalized_facts=evidence.extracted_facts,
                    extractor_type="deterministic_queue_bridge",
                    retrieved_at=evidence.retrieved_at,
                    evidence_strength="high" if evidence.id in {owner_claim.evidence_id, transition_claim.evidence_id} else "medium",
                    explanation="Source evidence copied from the immutable research case; model output is not source fact.",
                    classification=evidence.classification,
                )
            self.db.add(copied)
            copied_evidence.append(copied)
        self.db.flush()
        record_score_assessment(
            self.db,
            candidate,
            owner_score=owner_score,
            signal_score=signal_score,
            factors=[
                {"axis": "owner_business", "feature": "accepted_owner_claim", "impact": owner_score, "claim_id": owner_claim.id},
                {"axis": "signal_identity", "feature": "transition_identity_claim", "impact": signal_score, "claim_id": transition_claim.id},
            ],
            evidence_ids=[evidence.id for evidence in copied_evidence],
        )
        self.db.add(
            ReviewCase(
                candidate_id=candidate.id,
                assigned_user=analyst_name,
                status="open",
                analyst_notes=[{
                    "note": "Promoted after accepted Milestone 4.7 proposal; unresolved fields remain explicit.",
                    "author": analyst_name,
                    "user_id": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }],
                decision_reason_codes=["accepted_evidence_bounded_proposal"],
            )
        )
        case.person_id = person.id
        case.business_id = business.id
        case.transition_signal_id = signal.id
        case.candidate_match_id = candidate.id
        case.status = "promoted_to_review"
        self.db.add(
            AuditEvent(
                candidate_id=candidate.id,
                actor=analyst_name,
                action="candidate_created_from_research",
                after_state={
                    "status": candidate.status,
                    "research_case_id": case.id,
                    "proposal_id": proposal.id,
                    "disposition_id": accepted.id,
                },
                detail="Evidence-backed Utah case entered human review; no validation decision was made.",
            )
        )
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def _claim(self, case_id: int, claim_id: int) -> EvidenceClaim:
        claim = self.db.get(EvidenceClaim, claim_id)
        if claim is None or claim.case_id != case_id:
            raise ValueError("Queue claim must belong to the research case")
        return claim

    @staticmethod
    def _claim_names(claim: EvidenceClaim, subject_name: str) -> bool:
        return str(claim.object_value.get("person", "")).casefold() == subject_name.casefold()

    def _source_for_evidence(self, evidence: CaseEvidence, state: str) -> Source:
        existing = self.db.scalar(
            select(Source).where(Source.canonical_url == evidence.canonical_url, Source.is_demo.is_(False))
        )
        if existing:
            return existing
        source = Source(
            source_type=evidence.source_type,
            publisher=evidence.publisher,
            canonical_url=evidence.canonical_url,
            retrieved_at=evidence.retrieved_at,
            published_at=evidence.published_at,
            jurisdiction=state,
            source_metadata={"case_evidence_id": evidence.id, "content_hash": evidence.content_hash},
            reliability="medium",
            is_demo=False,
        )
        self.db.add(source)
        self.db.flush()
        return source


def _claim_score(claim: EvidenceClaim, base: int) -> int:
    authority = AUTHORITY_MULTIPLIERS.get(claim.source_authority, 0.4)
    directness = DIRECTNESS_MULTIPLIERS.get(claim.directness, 0.4)
    classification = 1.0 if claim.classification == "source_fact" else 0.7
    return max(0, min(100, round(base * claim.confidence * authority * directness * classification)))


def _split_person_name(value: str) -> tuple[str, str]:
    parts = value.split()
    if len(parts) < 2:
        raise ValueError("Queue subject requires at least a first and last name")
    return " ".join(parts[:-1]), parts[-1]
