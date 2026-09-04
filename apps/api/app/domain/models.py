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
