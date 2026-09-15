"""Reviewed handoffs over immutable decisions and briefs, with no enrichment."""
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select

from app.domain.models import CaseDecision, CaseBriefVersion
from app.research.discovery_runs import utc


class BusinessContact(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    source_id: int = Field(ge=1)
    recipient: str = Field(min_length=2, max_length=200)
    channel: Literal['email', 'phone', 'website', 'public_profile']
    value: str = Field(min_length=3, max_length=500)
    quote: str = Field(min_length=5, max_length=2000)
    public_business_use_reviewed: Literal[True]

    @model_validator(mode='after')
    def meaningful(self):
        if len(self.recipient.strip()) < 2 or len(self.value.strip()) < 3:
            raise ValueError('Provide a business recipient and contact value')
        if self.value not in self.quote:
            raise ValueError('Contact value must appear exactly in the selected source quotation')
        return self


class DevelopmentInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    summary: str = Field(min_length=10, max_length=2000)
    unknowns: str = Field(min_length=10, max_length=2000)
    readiness: Literal['not_ready', 'reviewer_ready']
    readiness_reason: str = Field(min_length=10, max_length=1000)
    contact: BusinessContact | None = None

    @model_validator(mode='after')
    def meaningful(self):
        if any(len(v.strip()) < 10 for v in [self.summary, self.unknowns, self.readiness_reason]):
            raise ValueError('Explain the opportunity, unknowns and readiness in at least ten characters each')
        if self.readiness == 'reviewer_ready' and self.contact is None:
            raise ValueError('Reviewer-ready communication requires a reviewed public business contact')
        return self


def validate_contact(development, sources):
    if development.contact is None:
        return
    contact = development.contact
    source = next((s for s in sources if s['id'] == contact.source_id), None)
    if source is None:
        raise ValueError('Contact source must belong to the exact saved brief version')
    if contact.quote not in source['relevant_excerpt']:
        raise ValueError('Contact quotation must appear exactly in the saved source excerpt')
    # Exact text proves traceability only. Public business use and readiness are
    # attributed reviewer judgments, never proof of consent or verified identity.


def handoff(db, case_id, decision_id):
    row = db.get(CaseDecision, decision_id)
    if row is None or row.case_id != case_id or row.content['outcome'] != 'create_development_brief':
        raise ValueError('Development brief not found in this case')
    brief = db.get(CaseBriefVersion, row.brief_id)
    successor = db.scalar(select(CaseDecision.id).where(CaseDecision.prior_id == row.id))
    contact = row.content['development'].get('contact')
    source = next((s for s in brief.content['sources'] if contact and s['id'] == contact['source_id']), None)
    return {
        'format': 'dealsage-development-brief-v1', 'case_id': case_id,
        'decision_id': row.id, 'reviewer': row.actor, 'reviewed_at': utc(row.created_at),
        'replaces_decision_id': row.prior_id, 'superseded_by_decision_id': successor,
        'reviewer_decision': row.content,
        'contact_provenance': source,
        'saved_brief': {'id': brief.id, 'version': brief.version, 'content_hash': brief.content_hash,
                        'saved_by': brief.actor, 'saved_at': utc(brief.created_at).isoformat(), 'content': brief.content},
        'boundaries': 'Internal reviewed handoff. Source reports, DealSage interpretation and human judgments remain distinct. '
                      'Readiness is the named reviewer’s assessment at the recorded time, not verified consent. '
                      'No ownership, successor, distress or sale intent follows from a name, role or death. Nothing has been sent.',
    }


def text_export(packet):
    """Plain text keeps untrusted source strings inert and preserves the full basis."""
    d = packet['reviewer_decision']; dev = d['development']; b = packet['saved_brief']
    sections = [
        'DEALSAGE — REVIEWED OPPORTUNITY-DEVELOPMENT HANDOFF', packet['boundaries'],
        f"Case {packet['case_id']} · Decision {packet['decision_id']} · Saved brief version {b['version']}",
        f"Reviewer: {packet['reviewer']} · Reviewed at: {packet['reviewed_at']}",
        f"Replaces decision: {packet['replaces_decision_id']} · Superseded by decision: {packet['superseded_by_decision_id']}",
        'HUMAN REVIEWER ASSESSMENT',
        f"Purpose: {d['purpose']}\nOpportunity: {dev['summary']}\nRationale: {d['rationale']}",
        f"Unknowns / limitations: {dev['unknowns']}\nNext action: {d['next_action']}",
        f"Communication readiness (reviewer judgment): {dev['readiness']}\nReason: {dev['readiness_reason']}",
        f"Supporting evidence IDs: {d['supporting_source_ids']}\nContradicting evidence IDs: {d['contradicting_source_ids']}",
        'PUBLIC BUSINESS CONTACT (REVIEWER SELECTED)',
        json.dumps(dev.get('contact'), ensure_ascii=False, indent=2) if dev.get('contact') else 'Unknown / not supplied. No recipient selected.',
        'CONTACT SOURCE / PUBLICATION AND RETRIEVAL DATES (null means unknown)',
        json.dumps(packet['contact_provenance'], ensure_ascii=False, indent=2),
        'FROZEN BASIS — SOURCE REPORTS, MODEL OBSERVATIONS, HUMAN REVIEWS AND UNRESOLVED QUESTIONS',
        json.dumps(b, ensure_ascii=False, indent=2),
        'COMPLETE REVIEWER DECISION / CORRECTION REASON',
        json.dumps(d, ensure_ascii=False, indent=2),
    ]
    return '\n\n'.join(sections) + '\n'
