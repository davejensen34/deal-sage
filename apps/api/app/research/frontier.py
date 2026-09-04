from datetime import datetime, timezone
import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import (
    CaseEvidence,
    EvidenceClaim,
    ResearchCase,
    ResearchFrontierItem,
    ResearchQuery,
    ResearchStep,
)
from app.research.ingestion import assert_safe_source_content


QUESTION_TYPES = frozenset(
    {
        "resolve_person_identity",
        "resolve_business_identity",
        "verify_relationship",
        "verify_transition_identity",
        "verify_operating_status",
        "resolve_contradiction",
        "find_independent_evidence",
    }
)
ACTION_TYPES = frozenset({"search", "retrieve", "extract", "model_analysis", "analyze"})
STEP_OUTCOMES = frozenset({"succeeded", "failed", "skipped"})
STOP_REASONS = frozenset(
    {
        "frontier_resolved",
        "frontier_empty",
        "frontier_attempts_exhausted",
        "step_budget_exhausted",
        "query_budget_exhausted",
        "document_budget_exhausted",
        "model_budget_exhausted",
        "time_budget_exhausted",
        "cost_budget_exhausted",
        "analyst_stopped",
        "safe_research_unavailable",
    }
)


class ResearchPlanner:
    """Own deterministic prioritization, budgets, and stops around research tools.

    Model output may eventually propose frontier items or actions, but this
    service remains the authority that decides whether an action may execute.
    """

    def __init__(self, db: Session):
        self.db = db

    def add_item(
        self,
        case_id: int,
        *,
        question_type: str,
        question: str,
        rationale: str,
        priority: int,
        supporting_claim_ids: list[int] | None = None,
        max_attempts: int = 2,
    ) -> ResearchFrontierItem:
        case = self._require_open_case(case_id)
        if question_type not in QUESTION_TYPES:
            raise ValueError("Unsupported research-frontier question type")
        if not question.strip() or len(question) > 500 or not rationale.strip():
            raise ValueError("Frontier items require a bounded question and rationale")
        if not 1 <= priority <= 100 or not 1 <= max_attempts <= 10:
            raise ValueError("Frontier priority or attempt limit is outside its bounds")
        claim_ids = list(dict.fromkeys(supporting_claim_ids or []))
        claims = self.db.scalars(
            select(EvidenceClaim).where(EvidenceClaim.id.in_(claim_ids))
        ).all()
        if len(claims) != len(claim_ids) or any(claim.case_id != case.id for claim in claims):
            raise ValueError("Frontier claims must all belong to the same research case")
        item = ResearchFrontierItem(
            case_id=case.id,
            question_type=question_type,
            question=question.strip(),
            rationale=rationale.strip(),
            priority=priority,
            supporting_claim_ids=claim_ids,
            max_attempts=max_attempts,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def next_item(self, case_id: int) -> ResearchFrontierItem | None:
        case = self._require_open_case(case_id)
        stop_reason = self._general_budget_stop(case)
        if stop_reason:
            self._stop(case, stop_reason)
            return None
        item = self.db.scalar(
            select(ResearchFrontierItem)
            .where(
                ResearchFrontierItem.case_id == case.id,
                ResearchFrontierItem.status == "pending",
                ResearchFrontierItem.attempts < ResearchFrontierItem.max_attempts,
            )
            .order_by(ResearchFrontierItem.priority.desc(), ResearchFrontierItem.id)
        )
        if item is not None:
            return item
        in_progress = self._count(
            ResearchFrontierItem.id,
            ResearchFrontierItem.case_id == case.id,
            ResearchFrontierItem.status == "in_progress",
        )
        if in_progress:
            # An active tool call is neither a terminal outcome nor exhausted work.
            return None
        total = self._count(ResearchFrontierItem.id, ResearchFrontierItem.case_id == case.id)
        unresolved = self._count(
            ResearchFrontierItem.id,
            ResearchFrontierItem.case_id == case.id,
            ResearchFrontierItem.status.not_in(("resolved", "cancelled")),
        )
        reason = "frontier_empty" if total == 0 else (
            "frontier_resolved" if unresolved == 0 else "frontier_attempts_exhausted"
        )
        self._stop(case, reason)
        return None

    def start_step(
        self,
        case_id: int,
        frontier_item_id: int,
        *,
        action_type: str,
        provider: str | None = None,
        model: str | None = None,
        prompt_version: str | None = None,
    ) -> ResearchStep:
        case = self._require_open_case(case_id)
        item = self.db.get(ResearchFrontierItem, frontier_item_id)
        if item is None or item.case_id != case.id or item.status != "pending":
            raise ValueError("Planner step requires a pending same-case frontier item")
        if action_type not in ACTION_TYPES:
            raise ValueError("Unsupported research action type")
        if action_type in {"search", "retrieve", "extract"} and not (
            provider and provider.strip()
        ):
            raise ValueError("External research actions require provider provenance")
        model_provenance = (provider, model, prompt_version)
        if action_type == "model_analysis" and not all(model_provenance):
            raise ValueError("Model analysis requires provider, model, and prompt version")
        if action_type != "model_analysis" and any((model, prompt_version)):
            raise ValueError("Model provenance is only valid for model analysis")
        stop_reason = self._action_budget_stop(case, action_type)
        if stop_reason:
            self._stop(case, stop_reason)
            raise ValueError(f"Research stopped: {stop_reason}")
        step_number = self._count(ResearchStep.id, ResearchStep.case_id == case.id) + 1
        step = ResearchStep(
            case_id=case.id,
            frontier_item_id=item.id,
            step_number=step_number,
            action_type=action_type,
            provider=provider.strip() if provider else None,
            model=model,
            prompt_version=prompt_version,
        )
        item.status = "in_progress"
        item.attempts += 1
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def complete_step(
        self,
        step_id: int,
        *,
        outcome: str,
        result_summary: dict[str, Any] | None = None,
        cost_cents: int = 0,
        error_class: str | None = None,
        resolves_item: bool = False,
    ) -> ResearchStep:
        step = self.db.get(ResearchStep, step_id)
        if step is None or step.status != "running":
            raise ValueError("Only a running research step can be completed")
        if outcome not in STEP_OUTCOMES or cost_cents < 0:
            raise ValueError("Invalid research-step outcome or cost")
        if error_class and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]{0,119}", error_class):
            raise ValueError("Research failures retain an exception class, not a message")
        summary = result_summary or {}
        assert_safe_source_content(summary)
        item = self.db.get(ResearchFrontierItem, step.frontier_item_id)
        if item is None:
            raise RuntimeError("Research step lost its frontier item")
        finished_at = datetime.now(timezone.utc)
        step.status = outcome
        step.finished_at = finished_at
        step.latency_ms = max(0, round((finished_at - _aware(step.started_at)).total_seconds() * 1000))
        step.cost_cents = cost_cents
        step.result_summary = summary
        # Persist only the exception class; provider messages and bodies are untrusted.
        step.error_class = error_class if outcome == "failed" and error_class else None
        if resolves_item:
            item.status = "resolved"
            item.resolved_at = finished_at
        elif item.attempts >= item.max_attempts:
            item.status = "blocked"
        else:
            item.status = "pending"
        self.db.commit()
        self.db.refresh(step)
        return step

    def stop_case(self, case_id: int, reason: str) -> ResearchCase:
        case = self._require_open_case(case_id)
        if reason not in {"analyst_stopped", "safe_research_unavailable"}:
            raise ValueError("Manual stops require an analyst or safe-research reason")
        self._stop(case, reason)
        return case

    def _action_budget_stop(self, case: ResearchCase, action_type: str) -> str | None:
        general = self._general_budget_stop(case)
        if general:
            return general
        if action_type == "search" and self._count(
            ResearchQuery.id, ResearchQuery.case_id == case.id
        ) >= self._limit(case, "max_queries"):
            return "query_budget_exhausted"
        if action_type == "retrieve" and self._count(
            CaseEvidence.id, CaseEvidence.case_id == case.id
        ) >= self._limit(case, "max_documents"):
            return "document_budget_exhausted"
        if action_type == "model_analysis" and self._count(
            ResearchStep.id,
            ResearchStep.case_id == case.id,
            ResearchStep.action_type == "model_analysis",
        ) >= self._limit(case, "max_model_calls"):
            return "model_budget_exhausted"
        return None

    def _general_budget_stop(self, case: ResearchCase) -> str | None:
        if self._count(ResearchStep.id, ResearchStep.case_id == case.id) >= self._limit(
            case, "max_steps"
        ):
            return "step_budget_exhausted"
        elapsed = (datetime.now(timezone.utc) - _aware(case.created_at)).total_seconds()
        if elapsed >= self._limit(case, "max_elapsed_seconds"):
            return "time_budget_exhausted"
        spent = self.db.scalar(
            select(func.coalesce(func.sum(ResearchStep.cost_cents), 0)).where(
                ResearchStep.case_id == case.id
            )
        ) or 0
        max_cost = self._limit(case, "max_cost_cents")
        if max_cost > 0 and spent >= max_cost:
            return "cost_budget_exhausted"
        return None

    def _stop(self, case: ResearchCase, reason: str) -> None:
        if reason not in STOP_REASONS:
            raise ValueError("Unsupported research stop reason")
        case.status = "stopped"
        case.stop_reason = reason
        case.stopped_at = datetime.now(timezone.utc)
        self.db.commit()

    def _require_open_case(self, case_id: int) -> ResearchCase:
        case = self.db.get(ResearchCase, case_id)
        if case is None:
            raise ValueError("Research case does not exist")
        if case.status != "open":
            raise ValueError("Research case is not open")
        return case

    def _count(self, column, *where) -> int:
        return int(self.db.scalar(select(func.count(column)).where(*where)) or 0)

    @staticmethod
    def _limit(case: ResearchCase, key: str) -> int:
        # Existing cases retain older JSON budget shapes across deployments.
        # Falling back here applies newly introduced limits without rewriting history.
        from app.research.cases import DEFAULT_RESEARCH_BUDGET

        return int(case.research_budget.get(key, DEFAULT_RESEARCH_BUDGET[key]))


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
