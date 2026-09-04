from __future__ import annotations
from datetime import date, datetime, timezone
from typing import Any
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Business(TimestampMixin, Base):
    __tablename__ = "businesses"
    id: Mapped[int] = mapped_column(primary_key=True)
    legal_name: Mapped[str] = mapped_column(String(200), index=True)
    doing_business_as: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(40), default="active")
    industry: Mapped[str | None] = mapped_column(String(120))
    website: Mapped[str | None] = mapped_column(String(300))
    phone: Mapped[str | None] = mapped_column(String(40))
    address: Mapped[str | None] = mapped_column(String(250))
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(20), index=True)
    postal_code: Mapped[str | None] = mapped_column(String(20))
    jurisdiction: Mapped[str | None] = mapped_column(String(100))
    registration_number: Mapped[str | None] = mapped_column(String(100))
    formation_date: Mapped[date | None] = mapped_column(Date)
    employee_range: Mapped[str | None] = mapped_column(String(60))
    revenue_range: Mapped[str | None] = mapped_column(String(60))
    ownership_type: Mapped[str | None] = mapped_column(String(80))


class Person(TimestampMixin, Base):
    __tablename__ = "people"
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    middle_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), index=True)
    suffix: Mapped[str | None] = mapped_column(String(30))
    aliases: Mapped[list[str]] = mapped_column(JSON, default=list)
    approximate_birth_year: Mapped[int | None] = mapped_column(Integer)
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(20))

    @property
    def full_name(self) -> str:
        return " ".join(filter(None, [self.first_name, self.middle_name, self.last_name, self.suffix]))


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(80))
    publisher: Mapped[str] = mapped_column(String(160))
    canonical_url: Mapped[str] = mapped_column(String(500))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    jurisdiction: Mapped[str | None] = mapped_column(String(100))
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    reliability: Mapped[str] = mapped_column(String(30), default="medium")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)


class AcquisitionRun(TimestampMixin, Base):
    """One bounded source attempt, including signal-first runs with no known business."""
    __tablename__ = "acquisition_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String(120), index=True)
    jurisdiction: Mapped[str] = mapped_column(String(80), index=True)
    discovery_strategy: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(30), default="running", index=True)
    contract_fingerprint: Mapped[str] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)


class RawArtifact(TimestampMixin, Base):
    """Content-addressed source response; its bytes are immutable in evidence storage."""
    __tablename__ = "raw_artifacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    source_key: Mapped[str] = mapped_column(String(120), index=True)
    source_record_id: Mapped[str | None] = mapped_column(String(200), index=True)
    canonical_url: Mapped[str] = mapped_column(String(1000))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    media_type: Mapped[str] = mapped_column(String(120))
    byte_size: Mapped[int] = mapped_column(Integer)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True)
    contract_fingerprint: Mapped[str] = mapped_column(String(64))
    request_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    __table_args__ = (UniqueConstraint("source_key", "content_hash", name="uq_raw_source_content"),)


class RunArtifact(Base):
    """Preserve every observation even when multiple runs retrieve identical bytes."""
    __tablename__ = "run_artifacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("acquisition_runs.id"), index=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("raw_artifacts.id"), index=True)
    __table_args__ = (UniqueConstraint("run_id", "artifact_id", name="uq_run_artifact"),)


class CuratedRecord(TimestampMixin, Base):
    """A parser outcome that may describe a person or signal before a business exists."""
    __tablename__ = "curated_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("raw_artifacts.id"), index=True)
    subject_key: Mapped[str] = mapped_column(String(240))
    subject_type: Mapped[str] = mapped_column(String(40), index=True)
    parser_version: Mapped[str] = mapped_column(String(80))
    schema_version: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), index=True)
    normalized_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    errors: Mapped[list[str]] = mapped_column(JSON, default=list)
    __table_args__ = (UniqueConstraint("artifact_id", "subject_key", "parser_version", name="uq_curated_artifact_subject_parser"),)


class FieldLineage(Base):
    __tablename__ = "field_lineage"
    id: Mapped[int] = mapped_column(primary_key=True)
    curated_record_id: Mapped[int] = mapped_column(ForeignKey("curated_records.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(160))
    raw_path: Mapped[str] = mapped_column(String(500))
    source_value_hash: Mapped[str] = mapped_column(String(64))
    __table_args__ = (UniqueConstraint("curated_record_id", "field_name", name="uq_curated_field_lineage"),)


class SignalResolution(TimestampMixin, Base):
    """Durable outcome of researching a person/signal without assuming a business."""
    __tablename__ = "signal_resolutions"
    id: Mapped[int] = mapped_column(primary_key=True)
    starting_record_id: Mapped[int] = mapped_column(ForeignKey("curated_records.id"), unique=True, index=True)
    business_record_id: Mapped[int | None] = mapped_column(ForeignKey("curated_records.id"), index=True)
    outcome: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    resolved_by: Mapped[str | None] = mapped_column(String(160))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ResearchCase(TimestampMixin, Base):
    """One evidence-convergence investigation, valid before any entity is resolved."""
    __tablename__ = "research_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    origin_strategy: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    person_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"), index=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id"), index=True)
    transition_signal_id: Mapped[int | None] = mapped_column(ForeignKey("transition_signals.id"), index=True)
    candidate_match_id: Mapped[int | None] = mapped_column(ForeignKey("candidate_matches.id"), index=True)
    research_budget: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    confidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    stop_reason: Mapped[str | None] = mapped_column(String(60), index=True)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CaseEvidence(TimestampMixin, Base):
    """Minimal public evidence retained for one case, not a reusable connector."""
    __tablename__ = "case_evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), index=True)
    known_source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), index=True)
    source_mode: Mapped[str] = mapped_column(String(40), index=True)
    canonical_url: Mapped[str] = mapped_column(String(1000))
    publisher: Mapped[str] = mapped_column(String(200))
    source_type: Mapped[str] = mapped_column(String(60), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    relevant_excerpt: Mapped[str | None] = mapped_column(Text)
    extracted_facts: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    classification: Mapped[str] = mapped_column(String(40), index=True)


class EvidenceClaim(TimestampMixin, Base):
    """One normalized assertion derived from case evidence, with precise semantics."""
    __tablename__ = "evidence_claims"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), index=True)
    evidence_id: Mapped[int] = mapped_column(ForeignKey("case_evidence.id"), index=True)
    subject_type: Mapped[str] = mapped_column(String(50), index=True)
    predicate: Mapped[str] = mapped_column(String(80), index=True)
    object_value: Mapped[dict[str, Any]] = mapped_column(JSON)
    relationship_semantics: Mapped[str | None] = mapped_column(String(60), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    classification: Mapped[str] = mapped_column(String(40), index=True)
    source_authority: Mapped[str] = mapped_column(String(30))
    directness: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="asserted", index=True)


class ResearchInference(TimestampMixin, Base):
    """A DealSage hypothesis supported by claims, never presented as source fact."""
    __tablename__ = "research_inferences"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), index=True)
    inference_type: Mapped[str] = mapped_column(String(80), index=True)
    statement: Mapped[str] = mapped_column(Text)
    supporting_claim_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(30), index=True)
    provider: Mapped[str | None] = mapped_column(String(60))
    model: Mapped[str | None] = mapped_column(String(120))
    prompt_version: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="proposed", index=True)


class ResearchQuery(TimestampMixin, Base):
    """One bounded search-provider call; query text stays inside its research case."""
    __tablename__ = "research_queries"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), index=True)
    query_text: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    max_results: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="running", index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    error_class: Mapped[str | None] = mapped_column(String(120))


class SourceCandidate(TimestampMixin, Base):
    """A dynamically discovered source that has not been promoted to a connector."""
    __tablename__ = "source_candidates"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), index=True)
    canonical_url: Mapped[str] = mapped_column(String(1000))
    domain: Mapped[str] = mapped_column(String(255), index=True)
    publisher: Mapped[str | None] = mapped_column(String(200))
    likely_source_type: Mapped[str] = mapped_column(String(60), index=True)
    geography: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    relevance_reason: Mapped[str] = mapped_column(Text)
    proposed_use: Mapped[str] = mapped_column(String(80), index=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    search_provider: Mapped[str] = mapped_column(String(80), index=True)
    access_observations: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="candidate", index=True)
    promoted_source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), index=True)
    promotion_reason: Mapped[str | None] = mapped_column(Text)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("case_id", "canonical_url", name="uq_source_candidate_case_url"),
    )


class SourceCandidateDiscovery(Base):
    """Retain every bounded query that independently surfaced a candidate."""
    __tablename__ = "source_candidate_discoveries"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("source_candidates.id"), index=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("research_queries.id"), index=True)
    result_rank: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        UniqueConstraint("candidate_id", "query_id", name="uq_candidate_query_discovery"),
    )


class ResearchFrontierItem(TimestampMixin, Base):
    """One unresolved case question eligible for bounded research."""
    __tablename__ = "research_frontier_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), index=True)
    question_type: Mapped[str] = mapped_column(String(80), index=True)
    question: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, index=True)
    supporting_claim_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=2)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ResearchStep(TimestampMixin, Base):
    """Auditable execution of one deterministic planner decision."""
    __tablename__ = "research_steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), index=True)
    frontier_item_id: Mapped[int] = mapped_column(
        ForeignKey("research_frontier_items.id"), index=True
    )
    step_number: Mapped[int] = mapped_column(Integer)
    action_type: Mapped[str] = mapped_column(String(40), index=True)
    provider: Mapped[str | None] = mapped_column(String(80))
    model: Mapped[str | None] = mapped_column(String(120))
    prompt_version: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    result_summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_class: Mapped[str | None] = mapped_column(String(120))
    __table_args__ = (
        UniqueConstraint("case_id", "step_number", name="uq_research_step_case_number"),
    )


class CaseAlias(TimestampMixin, Base):
    """An observed person or business alias with claim-level provenance."""
    __tablename__ = "case_aliases"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(30), index=True)
    canonical_value: Mapped[str] = mapped_column(String(240))
    alias_value: Mapped[str] = mapped_column(String(240))
    normalized_value: Mapped[str] = mapped_column(String(240), index=True)
    source_claim_id: Mapped[int] = mapped_column(ForeignKey("evidence_claims.id"), index=True)
    __table_args__ = (
        UniqueConstraint("case_id", "entity_type", "normalized_value", name="uq_case_alias_normalized"),
    )


class ClaimContradiction(TimestampMixin, Base):
    """A conflict between source claims; neither underlying assertion is erased."""
    __tablename__ = "claim_contradictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), index=True)
    left_claim_id: Mapped[int] = mapped_column(ForeignKey("evidence_claims.id"), index=True)
    right_claim_id: Mapped[int] = mapped_column(ForeignKey("evidence_claims.id"), index=True)
    contradiction_type: Mapped[str] = mapped_column(String(60), index=True)
    rationale: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    __table_args__ = (
        UniqueConstraint("case_id", "left_claim_id", "right_claim_id", name="uq_case_claim_conflict"),
    )


class EvidenceRelationship(TimestampMixin, Base):
    """Deterministic independence classification for a pair of evidence items."""
    __tablename__ = "evidence_relationships"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), index=True)
    left_evidence_id: Mapped[int] = mapped_column(ForeignKey("case_evidence.id"), index=True)
    right_evidence_id: Mapped[int] = mapped_column(ForeignKey("case_evidence.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(40), index=True)
    basis: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    __table_args__ = (
        UniqueConstraint("case_id", "left_evidence_id", "right_evidence_id", name="uq_case_evidence_pair"),
    )


class IdentityResolution(TimestampMixin, Base):
    """A reviewable bidirectional identity hypothesis, never a name-only merge."""
    __tablename__ = "identity_resolutions"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("research_cases.id"), index=True)
    direction: Mapped[str] = mapped_column(String(40), index=True)
    subject_value: Mapped[str] = mapped_column(String(240))
    candidate_value: Mapped[str] = mapped_column(String(240))
    supporting_claim_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    contradictory_claim_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    support_dimensions: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="proposed", index=True)


class BusinessRelationship(Base):
    __tablename__ = "business_relationships"
    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"))
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"))
    relationship_type: Mapped[str] = mapped_column(String(50))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    evidence_refs: Mapped[list[int]] = mapped_column(JSON, default=list)


class TargetProfile(TimestampMixin, Base):
    __tablename__ = "target_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    criteria: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ResearchTrail(TimestampMixin, Base):
    __tablename__ = "research_trails"
    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), unique=True)
    target_profile_id: Mapped[int | None] = mapped_column(ForeignKey("target_profiles.id"))
    owner_research_ready: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    readiness_explanation: Mapped[str] = mapped_column(Text, default="Insufficient evidence")
    business: Mapped[Business] = relationship()
    target_profile: Mapped[TargetProfile | None] = relationship()
    stages: Mapped[list[ResearchStage]] = relationship(back_populates="trail", cascade="all, delete-orphan", order_by="ResearchStage.sequence")


class ResearchStage(Base):
    __tablename__ = "research_stages"
    id: Mapped[int] = mapped_column(primary_key=True)
    trail_id: Mapped[int] = mapped_column(ForeignKey("research_trails.id"), index=True)
    stage_type: Mapped[str] = mapped_column(String(50), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), index=True)
    confidence: Mapped[int | None] = mapped_column(Integer)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))
    person_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"))
    relationship_id: Mapped[int | None] = mapped_column(ForeignKey("business_relationships.id"))
    evidence_refs: Mapped[list[int]] = mapped_column(JSON, default=list)
    supporting_evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    contradictions: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    detail: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    trail: Mapped[ResearchTrail] = relationship(back_populates="stages")
    source: Mapped[Source | None] = relationship()


class TransitionSignal(Base):
    __tablename__ = "transition_signals"
    id: Mapped[int] = mapped_column(primary_key=True)
    signal_type: Mapped[str] = mapped_column(String(50), index=True)
    published_name: Mapped[str] = mapped_column(String(200))
    possible_transition_date: Mapped[date | None] = mapped_column(Date)
    publication_date: Mapped[date | None] = mapped_column(Date)
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(20))
    age: Mapped[int | None] = mapped_column(Integer)
    relatives: Mapped[list[str]] = mapped_column(JSON, default=list)
    occupation_clues: Mapped[list[str]] = mapped_column(JSON, default=list)
    business_clues: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    extraction_confidence: Mapped[float] = mapped_column(Float, default=0)
    source: Mapped[Source] = relationship()


class CandidateMatch(TimestampMixin, Base):
    __tablename__ = "candidate_matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"))
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"))
    relationship_id: Mapped[int] = mapped_column(ForeignKey("business_relationships.id"))
    signal_id: Mapped[int] = mapped_column(ForeignKey("transition_signals.id"))
    owner_business_confidence: Mapped[int] = mapped_column(Integer)
    signal_identity_confidence: Mapped[int] = mapped_column(Integer)
    overall_candidate_confidence: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)
    match_explanation: Mapped[str] = mapped_column(Text)
    positive_signals: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    conflicting_signals: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    missing_evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommended_next_action: Mapped[str] = mapped_column(Text)
    last_researched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    person: Mapped[Person] = relationship()
    business: Mapped[Business] = relationship()
    relationship_record: Mapped[BusinessRelationship] = relationship()
    signal: Mapped[TransitionSignal] = relationship()
    evidence: Mapped[list[Evidence]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_matches.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(80))
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    subject_type: Mapped[str] = mapped_column(String(50))
    subject_id: Mapped[int] = mapped_column(Integer)
    extracted_text: Mapped[str] = mapped_column(Text)
    normalized_facts: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    extractor_type: Mapped[str] = mapped_column(String(50), default="deterministic")
    model_used: Mapped[str | None] = mapped_column(String(120))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    evidence_strength: Mapped[str] = mapped_column(String(30))
    explanation: Mapped[str] = mapped_column(Text)
    classification: Mapped[str] = mapped_column(String(30), default="source_fact")
    candidate: Mapped[CandidateMatch] = relationship(back_populates="evidence")
    source: Mapped[Source] = relationship()


class ReviewCase(TimestampMixin, Base):
    __tablename__ = "review_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate_matches.id"), unique=True)
    assigned_user: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), default="open")
    decision: Mapped[str | None] = mapped_column(String(30))
    analyst_notes: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    decision_reason_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("candidate_matches.id"), index=True)
    actor: Mapped[str] = mapped_column(String(120))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    action: Mapped[str] = mapped_column(String(80))
    before_state: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    after_state: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    detail: Mapped[str | None] = mapped_column(Text)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50))
    subject: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320))
    display_name: Mapped[str] = mapped_column(String(160))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint("provider", "subject", name="uq_users_provider_subject"),)


class AIExecution(Base):
    __tablename__ = "ai_executions"
    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("candidate_matches.id"))
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(40))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    token_usage: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean)
    error: Mapped[str | None] = mapped_column(Text)
