from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from app.domain.models import CandidateMatch, CandidateScoreAssessment, ReviewCase


EXPORT_SCHEMA_VERSION = "dealsage-candidate-export-v1"


def candidate_export_record(
    candidate: CandidateMatch,
    assessment: CandidateScoreAssessment | None,
    review: ReviewCase | None,
) -> dict[str, Any]:
    """Build the public-reference export without copying retained evidence content."""
    evidence = sorted(candidate.evidence, key=lambda item: item.id)
    retrieved = [item.retrieved_at for item in evidence]
    return {
        "candidate_id": candidate.id,
        "candidate_status": candidate.status,
        "business": {
            "legal_name": candidate.business.legal_name,
            "doing_business_as": candidate.business.doing_business_as,
            "status": candidate.business.status,
            "industry": candidate.business.industry,
            "city": candidate.business.city,
            "state": candidate.business.state,
            "jurisdiction": candidate.business.jurisdiction,
            "registration_number": candidate.business.registration_number,
        },
        "person": {"name": candidate.person.full_name},
        # A filing role is exported as the source-reported relationship, never
        # silently upgraded to beneficial ownership.
        "relationship": {
            "type": candidate.relationship_record.relationship_type,
            "active": candidate.relationship_record.active,
            "confidence": candidate.relationship_record.confidence,
            "classification": "source_reported_role",
        },
        "transition_signal": {
            "type": candidate.signal.signal_type,
            "possible_transition_date": candidate.signal.possible_transition_date,
            "publication_date": candidate.signal.publication_date,
            "classification": "source_fact",
            "source_reference": _source_reference(candidate.signal.source),
        },
        "score": {
            "business_relationship": candidate.owner_business_confidence,
            "signal_identity": candidate.signal_identity_confidence,
            "overall_candidate": candidate.overall_candidate_confidence,
            "method_version": assessment.method_version if assessment else None,
            "provenance_classification": assessment.provenance_classification if assessment else "unavailable",
            "factors": assessment.factors if assessment else [],
            "supporting_evidence_ids": assessment.supporting_evidence_ids if assessment else [],
            "calculation": assessment.calculation if assessment else {},
            "calculated_at": assessment.created_at if assessment else None,
            "interpretation": "deterministic_prioritization_not_source_fact",
        },
        "evidence_references": [
            {
                "evidence_id": item.id,
                "evidence_type": item.evidence_type,
                "classification": item.classification,
                "strength": item.evidence_strength,
                "retrieved_at": item.retrieved_at,
                "source": _source_reference(item.source),
            }
            for item in evidence
        ],
        "freshness": {
            "candidate_last_researched_at": candidate.last_researched_at,
            "oldest_evidence_retrieved_at": min(retrieved) if retrieved else None,
            "newest_evidence_retrieved_at": max(retrieved) if retrieved else None,
        },
        "analyst_disposition": {
            "review_status": review.status,
            "decision": review.decision,
            "reason_codes": review.decision_reason_codes,
            "reviewed_at": review.reviewed_at,
        } if review else None,
    }


def export_envelope(records: list[dict[str, Any]], exported_by: str) -> dict[str, Any]:
    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc),
        "generated_by": exported_by,
        "record_count": len(records),
        "content_boundaries": {
            "raw_evidence_included": False,
            "extracted_evidence_text_included": False,
            "normalized_facts_included": False,
            "analyst_notes_included": False,
            "model_payloads_included": False,
        },
        "records": records,
    }


def candidate_export_csv(records: list[dict[str, Any]]) -> str:
    """Flatten the stable contract while retaining nested provenance as JSON."""
    output = io.StringIO()
    fields = [
        "schema_version", "candidate_id", "candidate_status", "business_name",
        "person_name", "state", "relationship_type", "relationship_classification",
        "signal_type", "possible_transition_date", "overall_candidate_score",
        "score_method_version", "score_provenance_classification", "score_factors_json",
        "supporting_evidence_ids_json", "evidence_references_json",
        "candidate_last_researched_at", "newest_evidence_retrieved_at",
        "analyst_decision", "analyst_reason_codes_json", "analyst_reviewed_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for record in records:
        review = record["analyst_disposition"] or {}
        writer.writerow({
            "schema_version": EXPORT_SCHEMA_VERSION,
            "candidate_id": record["candidate_id"],
            "candidate_status": record["candidate_status"],
            "business_name": record["business"]["legal_name"],
            "person_name": record["person"]["name"],
            "state": record["business"]["state"],
            "relationship_type": record["relationship"]["type"],
            "relationship_classification": record["relationship"]["classification"],
            "signal_type": record["transition_signal"]["type"],
            "possible_transition_date": _scalar(record["transition_signal"]["possible_transition_date"]),
            "overall_candidate_score": record["score"]["overall_candidate"],
            "score_method_version": record["score"]["method_version"],
            "score_provenance_classification": record["score"]["provenance_classification"],
            "score_factors_json": json.dumps(record["score"]["factors"], separators=(",", ":")),
            "supporting_evidence_ids_json": json.dumps(record["score"]["supporting_evidence_ids"]),
            "evidence_references_json": json.dumps(record["evidence_references"], default=_scalar, separators=(",", ":")),
            "candidate_last_researched_at": _scalar(record["freshness"]["candidate_last_researched_at"]),
            "newest_evidence_retrieved_at": _scalar(record["freshness"]["newest_evidence_retrieved_at"]),
            "analyst_decision": review.get("decision"),
            "analyst_reason_codes_json": json.dumps(review.get("reason_codes", [])),
            "analyst_reviewed_at": _scalar(review.get("reviewed_at")),
        })
    return output.getvalue()


def _source_reference(source: Any) -> dict[str, Any]:
    # Canonical query strings are unnecessary for lineage and may contain
    # source-side session or access parameters, so integrations receive only
    # the stable public location.
    parts = urlsplit(source.canonical_url)
    safe_url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    return {
        "source_id": source.id,
        "source_type": source.source_type,
        "publisher": source.publisher,
        "canonical_url": safe_url,
        "published_at": source.published_at,
        "retrieved_at": source.retrieved_at,
        "reliability": source.reliability,
    }


def _scalar(value: Any) -> str:
    if value is None:
        return ""
    return value.isoformat() if hasattr(value, "isoformat") else str(value)
