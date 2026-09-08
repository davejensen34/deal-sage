"""Execute the explicitly approved Milestone 4 evaluation into an isolated database."""

import argparse
import asyncio
from datetime import datetime, timezone
from html import unescape
import json
from pathlib import Path
import re
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.openai import OpenAIProvider
from app.core.config import Settings
from app.core.database import Base
from app.domain.models import ModelProposal, RawArtifact, ResearchCase, ResearchQuery, SourceCandidate
from app.research.cases import ResearchCaseService
from app.research.evaluation_protocol import PROTOCOL_ID, validate_manifest
from app.research.model_analysis import ModelAnalysisService
from app.research.retrieval import CandidateRetrievalService, HttpDocumentProvider
from app.research.search import SearchService
from app.research.search_openai import OpenAIWebSearchProvider
from app.storage.local import LocalEvidenceStorage


SEARCH_ESTIMATE_CENTS = 2  # $0.01 tool fee plus a conservative content-token reserve.


class ProtocolStop(RuntimeError):
    """End the governed run without retrying or advancing to another case."""

    def __init__(self, reason: str, partial_case: dict[str, Any]):
        super().__init__(reason)
        self.reason = reason
        self.partial_case = partial_case


async def execute_case(
    db: Session,
    case_spec: dict[str, Any],
    *,
    search_provider: OpenAIWebSearchProvider,
    model_providers: dict[str, Any],
    storage: LocalEvidenceStorage,
    existing_case: ResearchCase | None = None,
) -> dict[str, Any]:
    cases = ResearchCaseService(db)
    case = existing_case or cases.create_case(
        case_spec["origin"], {
            "max_queries": 2,
            "max_documents": 5,
            "max_model_calls": 4,
            "max_steps": 20,
            "max_elapsed_seconds": 1_200,
            "max_cost_cents": case_spec["max_cost_cents"],
        },
    )
    search_service = SearchService(db)
    prior_query = db.scalar(select(ResearchQuery).where(ResearchQuery.case_id == case.id))
    search_candidates = (
        db.scalars(select(SourceCandidate).where(SourceCandidate.case_id == case.id)).all()
        if prior_query is not None
        else await search_service.execute(case.id, search_provider, case_spec["query"], max_results=5)
    )
    retrievals: list[dict[str, Any]] = []
    evidence_ids: list[int] = []
    claim_ids: list[int] = []
    retrieval = CandidateRetrievalService(db, storage)
    http = HttpDocumentProvider()

    for source in case_spec["sources"]:
        candidate = db.scalar(
            select(SourceCandidate).where(
                SourceCandidate.case_id == case.id,
                SourceCandidate.canonical_url == source["url"],
            )
        )
        if candidate is None:
            candidate = SourceCandidate(
                case_id=case.id,
                canonical_url=source["url"],
                domain=source["url"].split("/", 3)[2].lower(),
                publisher=source["publisher"],
                likely_source_type=source["source_type"],
                geography={"state": case_spec["state"]},
                relevance_reason="Prequalified public anchor in the approved manifest.",
                proposed_use="case_specific_research",
                search_provider="approved_manifest",
                access_observations={"prior_public_qualification": True},
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
        if candidate.access_decision == "pending":
            search_service.decide_access(
                candidate.id,
                decision="approved",
                reason="Ordinary public page approved in the frozen protocol; no access control observed during qualification.",
                decided_by="Protocol m4-e2e-v1-2026-09-08",
            )
        try:
            evidence = await retrieval.retrieve(case.id, candidate.id, http)
            artifact = db.get(RawArtifact, evidence.raw_artifact_id)
            if artifact is None:
                raise RuntimeError("Retrieved evidence lost its immutable artifact")
            raw_text = storage.read(artifact.storage_key).decode("utf-8", errors="replace")
            page_text = _visible_text(raw_text)
            excerpt = _find_excerpt(page_text, source["excerpt"])
            evidence.relevant_excerpt = excerpt
            evidence.extracted_facts = {
                "subject": case_spec["subject"],
                "business": case_spec["business"],
            }
            db.commit()
            evidence_ids.append(evidence.id)
            for claim_spec in source["claims"]:
                claim = cases.add_claim(
                    case.id,
                    evidence.id,
                    subject_type=claim_spec["subject_type"],
                    predicate=claim_spec["predicate"],
                    object_value=claim_spec["object_value"],
                    relationship_semantics=claim_spec["relationship_semantics"],
                    confidence=0.9,
                    classification="source_fact",
                    source_authority="publisher",
                    directness="explicit",
                )
                claim_ids.append(claim.id)
            retrievals.append({"url": source["url"], "status": "succeeded", "evidence_id": evidence.id})
        except Exception as exc:
            retrievals.append({"url": source["url"], "status": "failed", "error_class": type(exc).__name__})
            # A frozen anchor that cannot reproduce is a protocol-integrity
            # failure, not permission to swap sources after seeing live output.
            raise ProtocolStop(
                f"qualified_source_failed:{type(exc).__name__}",
                _case_result(case_spec, case.id, search_candidates, retrievals, []),
            ) from exc

    proposals: list[ModelProposal] = []
    if evidence_ids:
        analysis = ModelAnalysisService(db)
        provider_order = ["openai", "anthropic"] if case_spec["slot"] != "M4-UT-1" else ["anthropic", "openai"]
        for provider_name in provider_order:
            provider = model_providers[provider_name]
            proposals.append(
                await analysis.extract_business(
                    case.id,
                    provider,
                    provider_name=provider_name,
                    model=provider.model,
                    evidence_ids=evidence_ids,
                    claim_ids=claim_ids,
                )
            )
            proposals.append(
                await analysis.analyze_ambiguity(
                    case.id,
                    provider,
                    provider_name=provider_name,
                    model=provider.model,
                    evidence_ids=evidence_ids,
                    claim_ids=claim_ids,
                )
            )

    return _case_result(case_spec, case.id, search_candidates, retrievals, proposals)


def _case_result(
    case_spec: dict[str, Any],
    case_id: int,
    search_candidates: list[SourceCandidate],
    retrievals: list[dict[str, Any]],
    proposals: list[ModelProposal],
) -> dict[str, Any]:
    return {
        "slot": case_spec["slot"],
        "case_id": case_id,
        "prelabel": case_spec["prelabel"],
        "search": {
            "query": case_spec["query"],
            "candidate_count": len(search_candidates),
            "domains": sorted({candidate.domain for candidate in search_candidates}),
        },
        "retrievals": retrievals,
        "proposals": [_proposal_result(proposal) for proposal in proposals],
    }


def _visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", without_scripts)).split())


def _find_excerpt(page_text: str, qualified_excerpt: str) -> str:
    normalized = " ".join(qualified_excerpt.split())
    if normalized.casefold() not in page_text.casefold():
        raise ValueError("Qualified excerpt was not present in the retrieved document")
    return normalized


def _proposal_result(proposal: ModelProposal) -> dict[str, Any]:
    return {
        "id": proposal.id,
        "task": proposal.task,
        "provider": proposal.provider,
        "model": proposal.model,
        "outcome": proposal.execution_outcome,
        "output": proposal.proposed_output,
        "input_tokens": proposal.input_tokens,
        "output_tokens": proposal.output_tokens,
        "latency_ms": proposal.latency_ms,
        "cost_cents": proposal.cost_cents,
        "error_class": proposal.error_class,
    }


async def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--approved-protocol-id", required=True)
    parser.add_argument("--confirm-live-calls", action="store_true")
    args = parser.parse_args()
    if not args.confirm_live_calls:
        parser.error("pass --confirm-live-calls to execute the approved protocol")

    manifest = json.loads(args.manifest.read_text())
    validate_manifest(manifest, args.approved_protocol_id)
    settings = Settings()
    if not settings.openai_api_key or not settings.anthropic_api_key:
        raise SystemExit("Both approved provider keys are required")
    if settings.openai_model != manifest["providers"]["openai"] or settings.anthropic_model != manifest["providers"]["anthropic"]:
        raise SystemExit("Configured models differ from the approved manifest")

    engine = create_engine(f"sqlite:///{args.database.resolve()}")
    Base.metadata.create_all(engine)
    providers = {
        "openai": OpenAIProvider(settings.openai_api_key, settings.openai_model, max_output_tokens=1000),
        "anthropic": AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model, max_output_tokens=1000),
    }
    search_provider = OpenAIWebSearchProvider(
        settings.openai_api_key, settings.openai_model, max_output_tokens=300
    )
    results: list[dict[str, Any]] = []
    stop_reason: str | None = None
    with Session(engine) as db:
        existing_cases = db.scalars(select(ResearchCase).order_by(ResearchCase.id)).all()
        for index, case_spec in enumerate(manifest["cases"]):
            try:
                result = await execute_case(
                    db,
                    case_spec,
                    search_provider=search_provider,
                    model_providers=providers,
                    storage=LocalEvidenceStorage(args.evidence_dir),
                    existing_case=existing_cases[index] if index < len(existing_cases) else None,
                )
            except ProtocolStop as exc:
                result = exc.partial_case
                stop_reason = exc.reason
            results.append(result)
            spent = len(results) * SEARCH_ESTIMATE_CENTS + sum(
                proposal["cost_cents"]
                for result in results
                for proposal in result["proposals"]
            )
            if spent > manifest["max_cost_cents"]:
                raise RuntimeError("Evaluation exceeded the approved total cost ceiling")
            case_spend = SEARCH_ESTIMATE_CENTS + sum(
                proposal["cost_cents"] for proposal in results[-1]["proposals"]
            )
            if case_spend > case_spec["max_cost_cents"]:
                raise RuntimeError("Evaluation exceeded the approved case cost ceiling")
            live_calls = len(results) + sum(len(result["proposals"]) for result in results)
            if live_calls > manifest["max_live_calls"]:
                raise RuntimeError("Evaluation exceeded the approved live-call ceiling")
            if stop_reason is not None:
                break
    payload = {
        "protocol_id": PROTOCOL_ID,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "estimated_cost_cents": len(results) * SEARCH_ESTIMATE_CENTS
        + sum(proposal["cost_cents"] for result in results for proposal in result["proposals"]),
        "live_calls": len(results) + sum(len(result["proposals"]) for result in results),
        "status": "stopped" if stop_reason else "completed",
        "stop_reason": stop_reason,
        "cases": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"live_calls": payload["live_calls"], "estimated_cost_cents": payload["estimated_cost_cents"]}))


if __name__ == "__main__":
    asyncio.run(run())
