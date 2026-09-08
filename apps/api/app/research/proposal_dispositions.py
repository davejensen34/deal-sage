"""Human disposition records for immutable model proposals."""

from typing import Any

from sqlalchemy.orm import Session

from app.domain.models import ModelProposal, ModelProposalDisposition, User
from app.research.ingestion import assert_safe_source_content
from app.research.model_proposals import ModelProposalService


DECISIONS = frozenset({"accept", "correct", "reject", "defer"})


class ModelProposalDispositionService:
    """Record analyst judgment without rewriting provider output or source facts."""

    def __init__(self, db: Session):
        self.db = db
        self.proposals = ModelProposalService(db)

    def add(
        self,
        proposal_id: int,
        *,
        analyst_name: str,
        decision: str,
        rationale: str,
        corrected_output: dict[str, Any] | None = None,
        supporting_evidence_ids: list[int] | None = None,
        supporting_claim_ids: list[int] | None = None,
        user_id: int | None = None,
    ) -> ModelProposalDisposition:
        proposal = self.db.get(ModelProposal, proposal_id)
        if proposal is None:
            raise ValueError("Model proposal does not exist")
        if decision not in DECISIONS:
            raise ValueError("Unsupported model-proposal disposition")
        if not analyst_name.strip() or not rationale.strip():
            raise ValueError("Proposal disposition requires analyst and rationale")
        if user_id is not None and self.db.get(User, user_id) is None:
            raise ValueError("Proposal disposition user does not exist")
        if decision in {"accept", "correct"} and proposal.execution_outcome != "completed":
            raise ValueError("Only a completed proposal may be accepted or corrected")
        if decision == "correct":
            if not corrected_output:
                raise ValueError("Corrected disposition requires corrected output")
            assert_safe_source_content(corrected_output)
        elif corrected_output is not None:
            raise ValueError("Corrected output is valid only for a correction")

        evidence_ids = _unique_ids(
            supporting_evidence_ids
            if supporting_evidence_ids is not None
            else proposal.supported_evidence_ids
        )
        claim_ids = _unique_ids(
            supporting_claim_ids
            if supporting_claim_ids is not None
            else proposal.supported_claim_ids
        )
        self.proposals.validate_lineage(proposal.case_id, evidence_ids, claim_ids)
        disposition = ModelProposalDisposition(
            proposal_id=proposal.id,
            case_id=proposal.case_id,
            user_id=user_id,
            analyst_name=analyst_name.strip(),
            decision=decision,
            rationale=rationale.strip(),
            corrected_output=corrected_output,
            supporting_evidence_ids=evidence_ids,
            supporting_claim_ids=claim_ids,
        )
        self.db.add(disposition)
        self.db.commit()
        self.db.refresh(disposition)
        return disposition


def _unique_ids(values: list[int]) -> list[int]:
    if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in values):
        raise ValueError("Disposition lineage IDs must be positive integers")
    if len(values) != len(set(values)):
        raise ValueError("Disposition lineage IDs must be unique")
    return values
