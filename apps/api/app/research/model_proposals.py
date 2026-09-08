"""Persistence boundary for safe, evidence-bounded model proposals."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import CaseEvidence, EvidenceClaim, ModelProposal, ResearchCase
from app.research.ingestion import assert_safe_source_content


PROPOSAL_TASKS = frozenset({"business_extraction", "match_analysis", "evidence_synthesis", "research_plan"})
EXECUTION_OUTCOMES = frozenset({"completed", "incomplete", "refusal", "invalid", "failed"})


class ModelProposalService:
    """Validate the complete execution record before one immutable insert."""

    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        case_id: int,
        *,
        task: str,
        provider: str,
        model: str,
        prompt_version: str,
        schema_version: str,
        execution_outcome: str,
        proposed_output: dict[str, Any] | None = None,
        supported_evidence_ids: list[int] | None = None,
        supported_claim_ids: list[int] | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
        latency_ms: int | None = None,
        cost_cents: int = 0,
        error_class: str | None = None,
    ) -> ModelProposal:
        if self.db.get(ResearchCase, case_id) is None:
            raise ValueError("Model proposal requires an existing research case")
        if task not in PROPOSAL_TASKS:
            raise ValueError("Unsupported model proposal task")
        if execution_outcome not in EXECUTION_OUTCOMES:
            raise ValueError("Unsupported model execution outcome")
        if not all(value.strip() for value in (provider, model, prompt_version, schema_version)):
            raise ValueError("Model proposal requires complete provider and version provenance")

        evidence_ids = _unique_ids(supported_evidence_ids or [], "evidence")
        claim_ids = _unique_ids(supported_claim_ids or [], "claim")
        self._require_case_lineage(case_id, evidence_ids, claim_ids)
        _validate_measures(input_tokens, output_tokens, total_tokens, latency_ms, cost_cents)

        if execution_outcome == "completed":
            if not proposed_output:
                raise ValueError("Completed model proposal requires structured output")
            if not evidence_ids and not claim_ids:
                raise ValueError("Completed model proposal requires evidence or claim lineage")
            if error_class is not None:
                raise ValueError("Completed model proposal cannot have an error class")
            assert_safe_source_content(proposed_output)
        else:
            # Invalid, refused, incomplete, and failed payloads may contain echoed
            # evidence or provider internals; preserve only their safe class.
            if proposed_output is not None:
                raise ValueError("Non-completed model execution cannot persist provider output")
            if not error_class or not error_class.strip():
                raise ValueError("Non-completed model execution requires an error class")

        proposal = ModelProposal(
            case_id=case_id,
            task=task,
            provider=provider.strip(),
            model=model.strip(),
            prompt_version=prompt_version.strip(),
            schema_version=schema_version.strip(),
            execution_outcome=execution_outcome,
            proposed_output=proposed_output,
            supported_evidence_ids=evidence_ids,
            supported_claim_ids=claim_ids,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_cents=cost_cents,
            error_class=error_class.strip() if error_class else None,
        )
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def _require_case_lineage(self, case_id: int, evidence_ids: list[int], claim_ids: list[int]) -> None:
        if evidence_ids:
            found = set(
                self.db.scalars(
                    select(CaseEvidence.id).where(
                        CaseEvidence.case_id == case_id, CaseEvidence.id.in_(evidence_ids)
                    )
                )
            )
            if found != set(evidence_ids):
                raise ValueError("Model proposal evidence must belong to the same research case")
        if claim_ids:
            claims = self.db.scalars(
                select(EvidenceClaim).where(
                    EvidenceClaim.case_id == case_id, EvidenceClaim.id.in_(claim_ids)
                )
            ).all()
            if {claim.id for claim in claims} != set(claim_ids):
                raise ValueError("Model proposal claims must belong to the same research case")
            if evidence_ids and not {claim.evidence_id for claim in claims}.issubset(set(evidence_ids)):
                raise ValueError("Model proposal claims must cite the supplied evidence set")


def _unique_ids(values: list[int], label: str) -> list[int]:
    if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in values):
        raise ValueError(f"Model proposal {label} IDs must be positive integers")
    if len(values) != len(set(values)):
        raise ValueError(f"Model proposal {label} IDs must be unique")
    return values


def _validate_measures(
    input_tokens: int | None,
    output_tokens: int | None,
    total_tokens: int | None,
    latency_ms: int | None,
    cost_cents: int,
) -> None:
    values = (input_tokens, output_tokens, total_tokens, latency_ms, cost_cents)
    if any(value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0) for value in values):
        raise ValueError("Model execution measures must be non-negative integers")
    if total_tokens is not None and input_tokens is not None and output_tokens is not None:
        if total_tokens != input_tokens + output_tokens:
            raise ValueError("Total tokens must equal the reported input and output token split")
