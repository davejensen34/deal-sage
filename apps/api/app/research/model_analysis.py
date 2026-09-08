"""Evidence-packet execution for structured extraction and ambiguity analysis."""

from dataclasses import dataclass
import json
from time import perf_counter
from typing import Any

from jsonschema import ValidationError, validate
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.providers.base import AIProvider, AIProviderOutputError, TokenUsage
from app.domain.models import CaseEvidence, EvidenceClaim, ModelProposal
from app.research.ingestion import assert_safe_source_content
from app.research.model_proposals import ModelProposalService


BUSINESS_FIELDS = (
    "legal_name",
    "doing_business_as",
    "industry",
    "website",
    "operating_status",
    "location",
    "reported_relationship",
)
BUSINESS_EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "enum": list(BUSINESS_FIELDS)},
                    "value": {"type": "string", "minLength": 1},
                    "evidence_ids": {"type": "array", "items": {"type": "integer"}, "minItems": 1, "uniqueItems": True},
                    "claim_ids": {"type": "array", "items": {"type": "integer"}, "uniqueItems": True},
                },
                "required": ["field", "value", "evidence_ids", "claim_ids"],
                "additionalProperties": False,
            },
        },
        "unresolved_questions": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["observations", "unresolved_questions", "summary"],
    "additionalProperties": False,
}

AMBIGUITY_ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "identity_status": {"type": "string", "enum": ["resolved", "ambiguous", "unresolved", "contradicted"]},
        "relationship": {"type": "string", "enum": ["current_owner", "former_owner", "successor", "non_owner_role", "unclear", "none"]},
        "relationship_time": {"type": "string", "enum": ["current_at_signal", "ended_before_signal", "ended_at_signal", "began_after_signal", "unclear", "not_applicable"]},
        "operating_status": {"type": "string", "enum": ["active", "inactive", "unknown"]},
        "support_dimensions": {"type": "array", "items": {"type": "string", "enum": ["relationship", "geography", "timeline", "registration"]}, "uniqueItems": True},
        "evidence_ids": {"type": "array", "items": {"type": "integer"}, "minItems": 1, "uniqueItems": True},
        "claim_ids": {"type": "array", "items": {"type": "integer"}, "uniqueItems": True},
        "contradictions": {"type": "array", "items": {"type": "string"}},
        "unresolved_questions": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["identity_status", "relationship", "relationship_time", "operating_status", "support_dimensions", "evidence_ids", "claim_ids", "contradictions", "unresolved_questions", "summary"],
    "additionalProperties": False,
}

OWNER_SUPPORT_SEMANTICS = frozenset({"owner", "co_owner"})


@dataclass(frozen=True)
class EvidencePacket:
    payload: dict[str, Any]
    evidence_ids: list[int]
    claim_ids: list[int]
    claims: list[EvidenceClaim]


class ModelAnalysisService:
    """Run one bounded provider task and persist only a validated proposal."""

    def __init__(self, db: Session):
        self.db = db
        self.proposals = ModelProposalService(db)

    async def extract_business(
        self,
        case_id: int,
        provider: AIProvider,
        *,
        provider_name: str,
        model: str,
        evidence_ids: list[int],
        claim_ids: list[int] | None = None,
        prompt_version: str = "business-extraction-v1",
    ) -> ModelProposal:
        packet = self._packet(case_id, evidence_ids, claim_ids or [])
        return await self._execute(
            case_id,
            provider,
            provider_name=provider_name,
            model=model,
            prompt_version=prompt_version,
            schema_version="business-extraction-v1",
            task="business_extraction",
            schema=BUSINESS_EXTRACTION_SCHEMA,
            instruction="Propose business observations using only the supplied evidence packet. Cite every observation.",
            packet=packet,
            validate_output=lambda output: _validate_business_output(output, packet),
        )

    async def analyze_ambiguity(
        self,
        case_id: int,
        provider: AIProvider,
        *,
        provider_name: str,
        model: str,
        evidence_ids: list[int],
        claim_ids: list[int] | None = None,
        prompt_version: str = "ambiguity-analysis-v1",
    ) -> ModelProposal:
        packet = self._packet(case_id, evidence_ids, claim_ids or [])
        return await self._execute(
            case_id,
            provider,
            provider_name=provider_name,
            model=model,
            prompt_version=prompt_version,
            schema_version="ambiguity-analysis-v1",
            task="match_analysis",
            schema=AMBIGUITY_ANALYSIS_SCHEMA,
            instruction="Analyze identity and relationship ambiguity using only the supplied evidence. Abstain when non-name support is insufficient.",
            packet=packet,
            validate_output=lambda output: _validate_ambiguity_output(output, packet),
        )

    def _packet(self, case_id: int, evidence_ids: list[int], claim_ids: list[int]) -> EvidencePacket:
        if not evidence_ids:
            raise ValueError("Model analysis requires at least one evidence item")
        self.proposals.validate_lineage(case_id, evidence_ids, claim_ids)
        evidence = self.db.scalars(
            select(CaseEvidence).where(CaseEvidence.id.in_(evidence_ids))
        ).all()
        claims = self.db.scalars(
            select(EvidenceClaim).where(EvidenceClaim.id.in_(claim_ids))
        ).all() if claim_ids else []
        evidence_by_id = {item.id: item for item in evidence}
        claims_by_id = {claim.id: claim for claim in claims}
        payload = {
            "case_id": case_id,
            "evidence": [
                {
                    "id": evidence_id,
                    "publisher": evidence_by_id[evidence_id].publisher,
                    "source_type": evidence_by_id[evidence_id].source_type,
                    "published_at": evidence_by_id[evidence_id].published_at.isoformat() if evidence_by_id[evidence_id].published_at else None,
                    "relevant_excerpt": evidence_by_id[evidence_id].relevant_excerpt,
                    "extracted_facts": evidence_by_id[evidence_id].extracted_facts,
                    "classification": evidence_by_id[evidence_id].classification,
                }
                for evidence_id in evidence_ids
            ],
            "claims": [
                {
                    "id": claim_id,
                    "evidence_id": claims_by_id[claim_id].evidence_id,
                    "subject_type": claims_by_id[claim_id].subject_type,
                    "predicate": claims_by_id[claim_id].predicate,
                    "object_value": claims_by_id[claim_id].object_value,
                    "relationship_semantics": claims_by_id[claim_id].relationship_semantics,
                    "classification": claims_by_id[claim_id].classification,
                }
                for claim_id in claim_ids
            ],
        }
        assert_safe_source_content(payload)
        return EvidencePacket(payload, evidence_ids, claim_ids, claims)

    async def _execute(
        self,
        case_id: int,
        provider: AIProvider,
        *,
        provider_name: str,
        model: str,
        prompt_version: str,
        schema_version: str,
        task: str,
        schema: dict[str, Any],
        instruction: str,
        packet: EvidencePacket,
        validate_output,
    ) -> ModelProposal:
        started = perf_counter()
        try:
            output = await provider.extract_structured(
                f"{instruction}\n\nEvidence packet:\n{json.dumps(packet.payload, sort_keys=True, default=str)}",
                schema,
            )
            validate(instance=output, schema=schema)
            validate_output(output)
            outcome = "completed"
            error_class = None
        except Exception as exc:
            output = None
            outcome = _execution_outcome(exc)
            error_class = type(exc).__name__
        usage = getattr(provider, "last_usage", TokenUsage())
        return self.proposals.record(
            case_id,
            task=task,
            provider=provider_name,
            model=model,
            prompt_version=prompt_version,
            schema_version=schema_version,
            execution_outcome=outcome,
            proposed_output=output,
            supported_evidence_ids=packet.evidence_ids,
            supported_claim_ids=packet.claim_ids,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            latency_ms=round((perf_counter() - started) * 1000),
            error_class=error_class,
        )


def _validate_business_output(output: dict[str, Any], packet: EvidencePacket) -> None:
    allowed_evidence = set(packet.evidence_ids)
    allowed_claims = set(packet.claim_ids)
    for observation in output["observations"]:
        cited_evidence = set(observation["evidence_ids"])
        cited_claim_ids = set(observation["claim_ids"])
        if not cited_evidence.issubset(allowed_evidence):
            raise ValueError("Business observation cites unsupported evidence")
        if not cited_claim_ids.issubset(allowed_claims):
            raise ValueError("Business observation cites unsupported claims")
        cited_claims = [claim for claim in packet.claims if claim.id in cited_claim_ids]
        if any(claim.evidence_id not in cited_evidence for claim in cited_claims):
            raise ValueError("Business observation claim falls outside its cited evidence")
        if observation["field"] == "reported_relationship" and observation["value"].casefold() in {
            "owner", "co-owner", "co_owner", "current owner", "current_owner"
        }:
            if not any(claim.relationship_semantics in OWNER_SUPPORT_SEMANTICS for claim in cited_claims):
                raise ValueError("Owner-role observation requires explicit owner-role claim support")


def _validate_ambiguity_output(output: dict[str, Any], packet: EvidencePacket) -> None:
    if not set(output["evidence_ids"]).issubset(set(packet.evidence_ids)):
        raise ValueError("Ambiguity analysis cites unsupported evidence")
    if not set(output["claim_ids"]).issubset(set(packet.claim_ids)):
        raise ValueError("Ambiguity analysis cites unsupported claims")
    if output["identity_status"] == "resolved" and not output["support_dimensions"]:
        raise ValueError("Resolved identity requires a non-name support dimension")
    if output["identity_status"] == "contradicted" and not output["contradictions"]:
        raise ValueError("Contradicted identity requires contradiction detail")
    valid_times = {
        "current_owner": {"current_at_signal", "ended_at_signal", "unclear"},
        "former_owner": {"ended_before_signal", "ended_at_signal", "unclear"},
        "successor": {"began_after_signal", "current_at_signal", "unclear"},
        "non_owner_role": {"current_at_signal", "ended_before_signal", "ended_at_signal", "unclear"},
        "unclear": {"unclear"},
        "none": {"not_applicable"},
    }
    if output["relationship_time"] not in valid_times[output["relationship"]]:
        raise ValueError("Relationship time conflicts with the proposed relationship")
    if output["relationship"] == "current_owner":
        cited_claims = [claim for claim in packet.claims if claim.id in output["claim_ids"]]
        if not any(claim.relationship_semantics in OWNER_SUPPORT_SEMANTICS for claim in cited_claims):
            raise ValueError("Current-owner proposal requires explicit owner-role claim support")


def _execution_outcome(exc: Exception) -> str:
    if isinstance(exc, AIProviderOutputError):
        return exc.outcome
    if isinstance(exc, (ValidationError, ValueError, TypeError)):
        return "invalid"
    return "failed"
