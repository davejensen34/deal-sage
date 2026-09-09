"""Record the approved Milestone 4.7 dispositions and promote the Utah case."""

import argparse
from copy import deepcopy
import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.domain.models import ModelProposal, ModelProposalDisposition
from app.research.proposal_dispositions import ModelProposalDispositionService
from app.research.review_queue import ResearchReviewQueueService, ReviewQueueSpec


ANALYST = "Dave Jensen"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    return parser.parse_args()


def _record(
    db: Session,
    proposal_id: int,
    decision: str,
    rationale: str,
    corrected_output: dict | None = None,
) -> ModelProposalDisposition:
    existing = db.scalar(
        select(ModelProposalDisposition).where(
            ModelProposalDisposition.proposal_id == proposal_id,
            ModelProposalDisposition.analyst_name == ANALYST,
            ModelProposalDisposition.decision == decision,
        )
    )
    if existing:
        return existing
    return ModelProposalDispositionService(db).add(
        proposal_id,
        analyst_name=ANALYST,
        decision=decision,
        rationale=rationale,
        corrected_output=corrected_output,
    )


def main() -> None:
    args = arguments()
    engine = create_engine(f"sqlite:///{args.database.resolve()}")
    with Session(engine) as db:
        utah_openai = db.get(ModelProposal, 32)
        utah_claude = db.get(ModelProposal, 33)
        texas_openai = db.get(ModelProposal, 34)
        if any(proposal is None for proposal in (utah_openai, utah_claude, texas_openai)):
            raise ValueError("Expected final Milestone 4.7 proposals are absent")
        if any("m4-7-ai-v4-2026-09-09" not in proposal.prompt_version for proposal in (utah_openai, utah_claude, texas_openai)):
            raise ValueError("Disposition target is outside the final approved protocol")

        deferred = _record(
            db,
            32,
            "defer",
            "The evidence supports an owner relationship at the transition, but the OpenAI result leaves its relationship and timeline open-ended. Follow-up is tracked in GitHub Issue #92.",
        )
        accepted = _record(
            db,
            33,
            "accept",
            "The cited obituary directly supports William Winger as owner at the transition. The proposal appropriately leaves successor and current Utah-franchise operation unresolved.",
        )
        corrected = deepcopy(texas_openai.proposed_output)
        corrected["operating_status"] = "active"
        corrected["summary"] = (
            f"{corrected['summary']} The Houston Texans remain active; this does not establish "
            "that Janice Suber McNair held an ownership interest at the transition."
        )
        texas = _record(
            db,
            34,
            "correct",
            "The non-owner conclusion is supported, but inactive described the person after death rather than the operating business. The business status is corrected to active.",
            corrected,
        )
        candidate = ResearchReviewQueueService(db).promote(
            ReviewQueueSpec(
                case_id=2,
                accepted_proposal_id=33,
                owner_claim_id=5,
                transition_claim_id=9,
                business_label="Utah franchise of APPS Paramedical",
                doing_business_as="APPS Paramedical",
                state="UT",
                missing_evidence=[
                    "Legal entity and registration for the Utah franchise",
                    "Successor or current owner after William Winger",
                    "Current operating status of the Utah franchise",
                ],
            ),
            analyst_name=ANALYST,
        )
        print(json.dumps({
            "dispositions": {
                "utah_openai": {"id": deferred.id, "decision": deferred.decision},
                "utah_claude": {"id": accepted.id, "decision": accepted.decision},
                "texas_openai": {"id": texas.id, "decision": texas.decision},
            },
            "candidate": {
                "id": candidate.id,
                "status": candidate.status,
                "owner_business_confidence": candidate.owner_business_confidence,
                "signal_identity_confidence": candidate.signal_identity_confidence,
                "overall_candidate_confidence": candidate.overall_candidate_confidence,
            },
        }))


if __name__ == "__main__":
    main()
