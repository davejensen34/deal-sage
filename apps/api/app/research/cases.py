from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import CaseEvidence, EvidenceClaim, ResearchCase, ResearchInference, Source
from app.research.ingestion import assert_safe_source_content


ORIGIN_STRATEGIES = frozenset({"signal_first", "business_first", "hybrid"})
SOURCE_MODES = frozenset({"case_specific_research", "persistent_connector"})
EVIDENCE_CLASSIFICATIONS = frozenset({"source_fact", "third_party_estimate"})
CLAIM_CLASSIFICATIONS = frozenset({"source_fact", "third_party_estimate"})
RELATIONSHIP_SEMANTICS = frozenset(
    {
        "owner",
        "co_owner",
        "founder",
        "operator",
        "family_business_participant",
        "executive",
        "employee",
        "former_owner",
        "sold_business",
        "retired",
        "registered_agent",
        "unknown",
    }
)
INFERENCE_METHODS = frozenset({"deterministic", "model_assisted"})
DEFAULT_RESEARCH_BUDGET = {
    "max_queries": 0,
    "max_documents": 10,
    "max_model_calls": 0,
    "max_steps": 20,
    "max_elapsed_seconds": 900,
    "max_cost_cents": 0,
}


class ResearchCaseService:
    """Build the evidence→claim→inference spine with deterministic boundaries."""

    def __init__(self, db: Session):
        self.db = db

    def create_case(
        self, origin_strategy: str, research_budget: dict[str, Any] | None = None
    ) -> ResearchCase:
        if origin_strategy not in ORIGIN_STRATEGIES:
            raise ValueError("Unsupported research-case origin strategy")
        unknown_limits = set(research_budget or {}) - set(DEFAULT_RESEARCH_BUDGET)
        if unknown_limits:
            raise ValueError("Research budget contains unsupported limits")
        budget = {**DEFAULT_RESEARCH_BUDGET, **(research_budget or {})}
        if any(not isinstance(value, int) or value < 0 for value in budget.values()):
            raise ValueError("Research budget values must be non-negative integers")
        case = ResearchCase(origin_strategy=origin_strategy, research_budget=budget)
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def add_evidence(
        self,
        case_id: int,
        *,
        source_mode: str,
        canonical_url: str,
        publisher: str,
        source_type: str,
        content: bytes,
        relevant_excerpt: str | None,
        extracted_facts: dict[str, Any],
        provenance: dict[str, Any],
        classification: str = "source_fact",
        published_at: datetime | None = None,
        known_source_id: int | None = None,
    ) -> CaseEvidence:
        self._require_case(case_id)
        if source_mode not in SOURCE_MODES:
            raise ValueError("Unsupported source-use mode")
        if classification not in EVIDENCE_CLASSIFICATIONS:
            raise ValueError("Unsupported evidence classification")
        if not canonical_url.startswith(("https://", "http://")):
            raise ValueError("Case evidence requires an HTTP(S) canonical URL")
        if not publisher.strip() or not source_type.strip() or not content:
            raise ValueError("Case evidence requires publisher, source type, and content")
        if relevant_excerpt is not None and len(relevant_excerpt) > 2_000:
            raise ValueError("Relevant excerpts are limited to 2,000 characters")
        if source_mode == "persistent_connector" and (
            known_source_id is None or self.db.get(Source, known_source_id) is None
        ):
            raise ValueError("Persistent connector evidence requires a known source")
        # Callers sanitize external responses before selecting facts. This final
        # guard prevents a future caller from persisting capability-like fields.
        assert_safe_source_content(extracted_facts)
        assert_safe_source_content(provenance)
        evidence = CaseEvidence(
            case_id=case_id,
            known_source_id=known_source_id,
            source_mode=source_mode,
            canonical_url=canonical_url,
            publisher=publisher.strip(),
            source_type=source_type.strip(),
            published_at=published_at,
            retrieved_at=datetime.now(timezone.utc),
            content_hash=sha256(content).hexdigest(),
            relevant_excerpt=relevant_excerpt,
            extracted_facts=extracted_facts,
            provenance=provenance,
            classification=classification,
        )
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def add_claim(
        self,
        case_id: int,
        evidence_id: int,
        *,
        subject_type: str,
        predicate: str,
        object_value: dict[str, Any],
        confidence: float,
        classification: str,
        source_authority: str,
        directness: str,
        relationship_semantics: str | None = None,
    ) -> EvidenceClaim:
        self._require_case(case_id)
        evidence = self.db.get(CaseEvidence, evidence_id)
        if evidence is None or evidence.case_id != case_id:
            raise ValueError("Claim evidence must belong to the same research case")
        if classification not in CLAIM_CLASSIFICATIONS:
            raise ValueError("Unsupported claim classification")
        if not 0 <= confidence <= 1:
            raise ValueError("Claim confidence must be between 0 and 1")
        if predicate == "relationship" and relationship_semantics not in RELATIONSHIP_SEMANTICS:
            raise ValueError("Relationship claims require precise supported semantics")
        claim = EvidenceClaim(
            case_id=case_id,
            evidence_id=evidence_id,
            subject_type=subject_type,
            predicate=predicate,
            object_value=object_value,
            relationship_semantics=relationship_semantics,
            confidence=confidence,
            classification=classification,
            source_authority=source_authority,
            directness=directness,
        )
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def add_inference(
        self,
        case_id: int,
        *,
        inference_type: str,
        statement: str,
        supporting_claim_ids: list[int],
        confidence: float,
        method: str,
        provider: str | None = None,
        model: str | None = None,
        prompt_version: str | None = None,
    ) -> ResearchInference:
        self._require_case(case_id)
        if not supporting_claim_ids:
            raise ValueError("An inference requires at least one supporting claim")
        if method not in INFERENCE_METHODS:
            raise ValueError("Unsupported inference method")
        if not 0 <= confidence <= 1:
            raise ValueError("Inference confidence must be between 0 and 1")
        claims = self.db.scalars(
            select(EvidenceClaim).where(EvidenceClaim.id.in_(supporting_claim_ids))
        ).all()
        if len({claim.id for claim in claims}) != len(set(supporting_claim_ids)) or any(
            claim.case_id != case_id for claim in claims
        ):
            raise ValueError("Inference claims must all belong to the same research case")
        if method == "model_assisted" and not all((provider, model, prompt_version)):
            raise ValueError("Model-assisted inference requires provider, model, and prompt version")
        inference = ResearchInference(
            case_id=case_id,
            inference_type=inference_type,
            statement=statement,
            supporting_claim_ids=list(dict.fromkeys(supporting_claim_ids)),
            confidence=confidence,
            method=method,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
        )
        self.db.add(inference)
        self.db.commit()
        self.db.refresh(inference)
        return inference

    def _require_case(self, case_id: int) -> ResearchCase:
        case = self.db.get(ResearchCase, case_id)
        if case is None:
            raise ValueError("Research case does not exist")
        return case
