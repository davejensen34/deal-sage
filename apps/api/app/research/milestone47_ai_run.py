"""One-shot governed execution for the approved Milestone 4.7 evidence cohort."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.openai import OpenAIProvider
from app.core.config import Settings
from app.domain.models import CaseEvidence, EvidenceClaim, ModelProposal, RawArtifact, ResearchCase
from app.research.cases import ResearchCaseService
from app.research.milestone47_ai_protocol import (
    EXPECTED_MODELS,
    FROZEN_PACKET_HASH,
    MAX_CASE_COST_CENTS,
    MAX_COST_CENTS,
    MAX_MODEL_CALLS,
    MAX_OUTPUT_TOKENS,
    validate_ai_manifest,
)
from app.research.model_analysis import ModelAnalysisService
from app.storage.local import LocalEvidenceStorage


ProviderFactory = Callable[[str, str, int, float], Any]


def verify_execution_inputs(
    db: Session,
    storage: LocalEvidenceStorage,
    manifest: dict[str, Any],
    frozen_packet_path: Path,
    approved_protocol_id: str,
) -> None:
    """Fail closed before provider construction if any approved input has drifted."""
    validate_ai_manifest(manifest, approved_protocol_id)
    if sha256(frozen_packet_path.read_bytes()).hexdigest() != FROZEN_PACKET_HASH:
        raise ValueError("Frozen packet file hash differs from the approved protocol")
    frozen = json.loads(frozen_packet_path.read_bytes())
    frozen_by_slot = {case["slot"]: case for case in frozen["cases"]}
    for case_spec in manifest["cases"]:
        frozen_case = frozen_by_slot.get(case_spec["slot"])
        if frozen_case is None or frozen_case["case_id"] != case_spec["case_id"]:
            raise ValueError("AI manifest case differs from the frozen packet")
        if [item["evidence_id"] for item in frozen_case["evidence"]] != case_spec["evidence_ids"]:
            raise ValueError("AI manifest evidence differs from the frozen packet")
        case = db.get(ResearchCase, case_spec["case_id"])
        if case is None or case.origin_strategy != case_spec["origin"]:
            raise ValueError("Research case is absent or has changed origin")
        for frozen_evidence in frozen_case["evidence"]:
            evidence = db.get(CaseEvidence, frozen_evidence["evidence_id"])
            artifact = db.get(RawArtifact, frozen_evidence["raw_artifact_id"])
            if evidence is None or artifact is None or evidence.case_id != case.id:
                raise ValueError("Frozen evidence lineage is absent")
            content = storage.read(artifact.storage_key)
            observed_hash = sha256(content).hexdigest()
            if observed_hash != frozen_evidence["content_hash"] or observed_hash != artifact.content_hash:
                raise ValueError("Frozen evidence artifact hash verification failed")


def ensure_manifest_claims(db: Session, manifest: dict[str, Any]) -> dict[str, list[int]]:
    """Persist the human-authored source claims once without changing their semantics."""
    service = ResearchCaseService(db)
    claim_ids: dict[str, list[int]] = {}
    for case_spec in manifest["cases"]:
        ids = []
        for claim_spec in case_spec["claims"]:
            candidates = db.scalars(
                select(EvidenceClaim).where(
                    EvidenceClaim.case_id == case_spec["case_id"],
                    EvidenceClaim.evidence_id == claim_spec["evidence_id"],
                    EvidenceClaim.subject_type == claim_spec["subject_type"],
                    EvidenceClaim.predicate == claim_spec["predicate"],
                    EvidenceClaim.relationship_semantics == claim_spec.get("relationship_semantics"),
                )
            ).all()
            existing = next(
                (claim for claim in candidates if claim.object_value == claim_spec["object_value"]),
                None,
            )
            claim = existing or service.add_claim(
                case_spec["case_id"],
                claim_spec["evidence_id"],
                subject_type=claim_spec["subject_type"],
                predicate=claim_spec["predicate"],
                object_value=claim_spec["object_value"],
                confidence=claim_spec["confidence"],
                classification=claim_spec["classification"],
                source_authority=claim_spec["source_authority"],
                directness=claim_spec["directness"],
                relationship_semantics=claim_spec.get("relationship_semantics"),
            )
            ids.append(claim.id)
        claim_ids[case_spec["slot"]] = ids
    return claim_ids


async def execute_approved_cohort(
    db: Session,
    settings: Settings,
    manifest: dict[str, Any],
    claim_ids_by_slot: dict[str, list[int]],
    *,
    provider_factory: ProviderFactory | None = None,
) -> dict[str, Any]:
    """Execute exactly the frozen matrix and stop on any lineage or budget breach."""
    if settings.ai_store_provider_responses:
        raise ValueError("Provider-side response storage must remain disabled")
    configured = {"openai": settings.openai_model, "anthropic": settings.anthropic_model}
    if configured != EXPECTED_MODELS:
        raise ValueError("Configured models differ from the approved protocol")
    if not settings.openai_api_key or not settings.anthropic_api_key:
        raise ValueError("Both approved provider credentials are required")
    if settings.ai_max_output_tokens != MAX_OUTPUT_TOKENS:
        raise ValueError("Configured output-token ceiling differs from the approved protocol")
    case_ids = [case["case_id"] for case in manifest["cases"]]
    approved_prompt_versions = [
        f"business-extraction-v1@{manifest['protocol_id']}",
        f"ambiguity-analysis-v1@{manifest['protocol_id']}",
    ]
    existing = db.scalars(
        select(ModelProposal).where(
            ModelProposal.case_id.in_(case_ids),
            ModelProposal.prompt_version.in_(approved_prompt_versions),
        )
    ).all()
    if existing:
        # A retry could turn a partial matrix into an incomparable experiment.
        # Preserve the first run and require an explicit replacement protocol.
        raise ValueError("Approved cohort already has model proposals; refusing a replay")

    factory = provider_factory or _live_provider
    analysis = ModelAnalysisService(db)
    results: list[dict[str, Any]] = []
    cases_by_slot = {case["slot"]: case for case in manifest["cases"]}
    case_costs = {slot: 0 for slot in cases_by_slot}
    for execution in manifest["execution_matrix"]:
        case_spec = cases_by_slot[execution["slot"]]
        provider_name = execution["provider"]
        task = execution["task"]
        if len(results) >= MAX_MODEL_CALLS:
            raise RuntimeError("Model call ceiling reached")
        model = EXPECTED_MODELS[provider_name]
        api_key = settings.openai_api_key if provider_name == "openai" else settings.anthropic_api_key
        provider = factory(provider_name, api_key, settings.ai_max_output_tokens, settings.ai_request_timeout_seconds)
        kwargs = {
            "case_id": case_spec["case_id"],
            "provider": provider,
            "provider_name": provider_name,
            "model": model,
            "evidence_ids": case_spec["evidence_ids"],
            "claim_ids": claim_ids_by_slot[case_spec["slot"]],
            "prompt_version": (
                f"business-extraction-v1@{manifest['protocol_id']}"
                if task == "business_extraction"
                else f"ambiguity-analysis-v1@{manifest['protocol_id']}"
            ),
        }
        proposal = (
            await analysis.extract_business(**kwargs)
            if task == "business_extraction"
            else await analysis.analyze_ambiguity(**kwargs)
        )
        case_costs[case_spec["slot"]] += proposal.cost_cents
        total_cost = sum(item["cost_cents"] for item in results) + proposal.cost_cents
        results.append(_safe_result(case_spec["slot"], proposal))
        if case_costs[case_spec["slot"]] > MAX_CASE_COST_CENTS or total_cost > MAX_COST_CENTS:
            raise RuntimeError("Recorded model usage exceeded the approved cost ceiling")

    return {
        "protocol_id": manifest["protocol_id"],
        "calls": len(results),
        "estimated_cost_cents": sum(item["cost_cents"] for item in results),
        "search_calls": 0,
        "results": results,
    }


def _live_provider(provider: str, api_key: str, max_output_tokens: int, timeout_seconds: float):
    if provider == "openai":
        return OpenAIProvider(api_key, EXPECTED_MODELS[provider], max_output_tokens=max_output_tokens, timeout_seconds=timeout_seconds)
    if provider == "anthropic":
        return AnthropicProvider(api_key, EXPECTED_MODELS[provider], max_output_tokens=max_output_tokens, timeout_seconds=timeout_seconds)
    raise ValueError("Provider is outside the approved protocol")


def _safe_result(slot: str, proposal: ModelProposal) -> dict[str, Any]:
    return {
        "slot": slot,
        "proposal_id": proposal.id,
        "task": proposal.task,
        "provider": proposal.provider,
        "model": proposal.model,
        "execution_outcome": proposal.execution_outcome,
        "proposed_output": proposal.proposed_output,
        "supported_evidence_ids": proposal.supported_evidence_ids,
        "supported_claim_ids": proposal.supported_claim_ids,
        "input_tokens": proposal.input_tokens,
        "output_tokens": proposal.output_tokens,
        "total_tokens": proposal.total_tokens,
        "latency_ms": proposal.latency_ms,
        "cost_cents": proposal.cost_cents,
        "error_class": proposal.error_class,
    }
