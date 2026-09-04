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
