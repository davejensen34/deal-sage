from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


Status = Literal["new", "researching", "needs_review", "validated", "rejected", "watchlist"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CandidateListItem(ORMModel):
    id: int
    business: str
    owner: str
    city: str | None
    state: str | None
    signal_type: str
    transition_date: date | None
    owner_business_confidence: int
    signal_identity_confidence: int
    overall_candidate_confidence: int
    status: str
    updated_at: datetime


class CandidatePage(BaseModel):
    items: list[CandidateListItem]
    total: int
    page: int
    page_size: int


class StatusUpdate(BaseModel):
    status: Status
    reason: str = Field(min_length=3)
    note: str = Field(min_length=3)


class NoteCreate(BaseModel):
    note: str = Field(min_length=1)


class BusinessOut(ORMModel):
    id: int
    legal_name: str
    doing_business_as: str | None
    status: str
    industry: str | None
    website: str | None
    address: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    registration_number: str | None
    employee_range: str | None
    revenue_range: str | None


class PersonOut(ORMModel):
    id: int
    full_name: str
    aliases: list[str]
    approximate_birth_year: int | None
    city: str | None
    state: str | None


class EvidenceOut(ORMModel):
    id: int
    evidence_type: str
    extracted_text: str
    normalized_facts: dict[str, Any]
    extractor_type: str
    model_used: str | None
    retrieved_at: datetime
    evidence_strength: str
    explanation: str
    classification: str
    source: dict[str, Any]


class CandidateDetail(BaseModel):
    id: int
    business: BusinessOut
    person: PersonOut
    relationship: dict[str, Any]
    signal: dict[str, Any]
    scores: dict[str, int]
    status: str
    match_explanation: str
    positive_signals: list[dict[str, Any]]
    conflicting_signals: list[dict[str, Any]]
    missing_evidence: list[str]
    recommended_next_action: str
    last_researched_at: datetime
    evidence: list[EvidenceOut]
    review: dict[str, Any] | None
    audit: list[dict[str, Any]]
