"""Deterministic execution of approved dynamic-research frontier work."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import (
    CaseEvidence,
    ModelProposal,
    ResearchFrontierItem,
    ResearchStep,
    SourceCandidate,
)
from app.research.frontier import ResearchPlanner
from app.research.retrieval import CandidateRetrievalService, DocumentProvider
from app.research.search import SearchProvider, SearchService
from app.storage.base import EvidenceStorage


@dataclass(frozen=True)
class LoopExecution:
    step: ResearchStep
    new_candidate_ids: tuple[int, ...] = ()
    evidence_id: int | None = None
    new_evidence: bool = False


class ResearchLoopService:
    """Execute one approved action; models never call tools through this class."""

    def __init__(self, db: Session):
        self.db = db
        self.planner = ResearchPlanner(db)
        self.search = SearchService(db)

    async def execute_search(
        self,
        case_id: int,
        frontier_item_id: int,
        provider: SearchProvider,
        *,
        query: str | None = None,
        max_results: int = 5,
    ) -> LoopExecution:
        item = self._require_item(case_id, frontier_item_id)
        approved_query = self._approved_search_query(item, query)
        before = set(
            self.db.scalars(
                select(SourceCandidate.id).where(SourceCandidate.case_id == case_id)
            )
        )
        step = self.planner.start_step(
            case_id, item.id, action_type="search", provider=provider.key
        )
        try:
            candidates = await self.search.execute(
                case_id, provider, approved_query, max_results=max_results
            )
            new_ids = tuple(candidate.id for candidate in candidates if candidate.id not in before)
            completed = self.planner.complete_step(
                step.id,
                outcome="succeeded",
                result_summary={
                    "candidate_count": len(candidates),
                    "new_candidate_count": len(new_ids),
                    "new_candidate_ids": list(new_ids),
                },
                resolves_item=bool(new_ids),
            )
            return LoopExecution(step=completed, new_candidate_ids=new_ids)
        except Exception as exc:
            self.planner.complete_step(
                step.id,
                outcome="failed",
                result_summary={"candidate_count": 0, "new_candidate_count": 0},
                error_class=type(exc).__name__,
            )
            raise

    async def execute_retrieval(
        self,
        case_id: int,
        frontier_item_id: int,
        candidate_id: int,
        provider: DocumentProvider,
        storage: EvidenceStorage,
    ) -> LoopExecution:
        item = self._require_item(case_id, frontier_item_id)
        self._require_approved_action(item, "retrieve")
        before = set(
            self.db.scalars(select(CaseEvidence.id).where(CaseEvidence.case_id == case_id))
        )
        step = self.planner.start_step(
            case_id, item.id, action_type="retrieve", provider=provider.key
        )
        try:
            evidence = await CandidateRetrievalService(self.db, storage).retrieve(
                case_id, candidate_id, provider
            )
            is_new = evidence.id not in before
            completed = self.planner.complete_step(
                step.id,
                outcome="succeeded",
                result_summary={
                    "candidate_id": candidate_id,
                    "evidence_id": evidence.id,
                    "new_evidence": is_new,
                    "content_hash": evidence.content_hash,
                },
                resolves_item=is_new,
            )
            return LoopExecution(
                step=completed, evidence_id=evidence.id, new_evidence=is_new
            )
        except Exception as exc:
            self.planner.complete_step(
                step.id,
                outcome="failed",
                result_summary={"candidate_id": candidate_id, "new_evidence": False},
                error_class=type(exc).__name__,
            )
            raise

    def next_item(self, case_id: int) -> ResearchFrontierItem | None:
        """Select work or persist the planner's deterministic terminal reason."""
        return self.planner.next_item(case_id)

    def _require_item(self, case_id: int, item_id: int) -> ResearchFrontierItem:
        item = self.db.get(ResearchFrontierItem, item_id)
        if item is None or item.case_id != case_id:
            raise ValueError("Research loop requires a same-case frontier item")
        return item

    def _approved_search_query(
        self, item: ResearchFrontierItem, supplied_query: str | None
    ) -> str:
        if item.proposal_id is None:
            if not supplied_query or not supplied_query.strip():
                raise ValueError("Analyst-created search work requires an explicit query")
            return supplied_query.strip()
        output = self._require_approved_action(item, "search")
        proposed_query = output.get("query")
        if not isinstance(proposed_query, str) or not proposed_query.strip():
            raise ValueError("Approved search proposal lacks a query")
        if supplied_query is not None and supplied_query.strip() != proposed_query.strip():
            raise ValueError("Execution query differs from the approved proposal")
        return proposed_query.strip()

    def _require_approved_action(
        self, item: ResearchFrontierItem, expected_action: str
    ) -> dict:
        if item.proposal_id is None:
            return {}
        proposal = self.db.get(ModelProposal, item.proposal_id)
        if proposal is None or proposal.execution_outcome != "completed":
            raise ValueError("Frontier item lost its completed proposal")
        output = proposal.proposed_output or {}
        if output.get("next_action") != expected_action:
            raise ValueError("Execution action differs from the approved proposal")
        return output
