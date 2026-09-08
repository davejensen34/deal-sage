"""Deterministic approval boundary for model-proposed research plans."""

from sqlalchemy.orm import Session

from app.domain.models import ModelProposal, ResearchFrontierItem
from app.research.frontier import ResearchPlanner


class ResearchPlanApprovalService:
    """Promote a safe proposal to the frontier without executing it."""

    def __init__(self, db: Session):
        self.db = db
        self.planner = ResearchPlanner(db)

    def approve(
        self,
        proposal_id: int,
        *,
        priority: int,
        max_attempts: int = 2,
    ) -> ResearchFrontierItem | None:
        proposal = self.db.get(ModelProposal, proposal_id)
        if proposal is None or proposal.task != "research_plan":
            raise ValueError("Approval requires a persisted research-plan proposal")
        if proposal.execution_outcome != "completed" or not proposal.proposed_output:
            raise ValueError("Only a completed research-plan proposal may be approved")
        existing = self.db.query(ResearchFrontierItem).filter_by(proposal_id=proposal.id).one_or_none()
        if existing is not None:
            raise ValueError("Research-plan proposal has already been approved")

        output = proposal.proposed_output
        if output["next_action"] == "stop":
            # A model can recommend stopping, but only the deterministic planner
            # or an analyst can close a case. Retain the proposal without mutation.
            return None
        action_detail = output["query"] or output["source_type"] or output["next_action"]
        return self.planner.add_item(
            proposal.case_id,
            question_type=output["question_type"],
            question=output["question"],
            rationale=f"{output['rationale']} Proposed action: {output['next_action']} ({action_detail}).",
            priority=priority,
            supporting_claim_ids=output["claim_ids"],
            max_attempts=max_attempts,
            proposal_id=proposal.id,
        )
