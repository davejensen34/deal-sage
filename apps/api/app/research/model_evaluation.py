"""Versioned, deterministic evaluation for evidence-bounded model observations."""

from dataclasses import asdict, dataclass
from typing import Any

from jsonschema import ValidationError, validate

from app.ai.providers.base import AIProviderOutputError, TokenUsage


DIMENSIONS = (
    "case_origin",
    "identity_resolution",
    "relationship",
    "relationship_time",
    "operating_status",
    "contradiction_state",
    "research_disposition",
)

EVALUATION_SCHEMA_V2: dict[str, Any] = {
    "type": "object",
    "properties": {
        "case_origin": {"type": "string", "enum": ["signal_first", "business_first", "hybrid"]},
        "identity_resolution": {
            "type": "string",
            "enum": ["resolved", "ambiguous", "unresolved", "contradicted"],
        },
        "relationship": {
            "type": "string",
            "enum": ["current_owner", "former_owner", "successor", "non_owner_role", "unclear", "none"],
        },
        "relationship_time": {
            "type": "string",
            "enum": ["current_at_signal", "ended_before_signal", "ended_at_signal", "began_after_signal", "unclear", "not_applicable"],
        },
        "operating_status": {"type": "string", "enum": ["active", "inactive", "unknown"]},
        "contradiction_state": {
            "type": "string",
            "enum": ["none", "resolved_by_timeline", "unresolved"],
        },
        "research_disposition": {
            "type": "string",
            "enum": ["candidate_supported", "needs_more_research", "no_qualifying_relationship", "no_business_found", "conflict_review"],
        },
        "supported_source_ids": {"type": "array", "items": {"type": "string"}},
        "contradictions": {"type": "array", "items": {"type": "string"}},
        "unresolved_questions": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": [*DIMENSIONS, "supported_source_ids", "contradictions", "unresolved_questions", "summary"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class EvaluationResult:
    provider_outcome: str
    output: dict[str, Any] | None
    dimension_matches: dict[str, bool] | None
    consistency_errors: list[str]
    usage: TokenUsage
    error_class: str | None = None
    error_reason: str | None = None


def consistency_errors(output: dict[str, Any], allowed_source_ids: set[str]) -> list[str]:
    """Detect contradictions without converting a model observation into truth."""

    errors: list[str] = []
    unknown_sources = sorted(set(output["supported_source_ids"]) - allowed_source_ids)
    if unknown_sources:
        errors.append(f"unsupported_source_ids:{','.join(unknown_sources)}")

    relationship = output["relationship"]
    relationship_time = output["relationship_time"]
    contradiction_state = output["contradiction_state"]
    disposition = output["research_disposition"]

    valid_times = {
        "current_owner": {"current_at_signal", "ended_at_signal", "unclear"},
        "former_owner": {"ended_before_signal", "ended_at_signal", "unclear"},
        "successor": {"began_after_signal", "current_at_signal", "unclear"},
        "non_owner_role": {"current_at_signal", "ended_before_signal", "ended_at_signal", "unclear"},
        "unclear": {"unclear"},
        "none": {"not_applicable"},
    }
    if relationship_time not in valid_times[relationship]:
        errors.append("relationship_time_conflicts_with_relationship")

    has_contradictions = bool(output["contradictions"])
    if contradiction_state == "none" and has_contradictions:
        errors.append("contradictions_present_when_state_is_none")
    if contradiction_state != "none" and not has_contradictions:
        errors.append("contradiction_state_requires_detail")

    if disposition == "candidate_supported" and (
        output["identity_resolution"] != "resolved"
        or relationship not in {"current_owner", "successor"}
        or output["operating_status"] != "active"
        or contradiction_state == "unresolved"
    ):
        errors.append("candidate_supported_without_required_resolved_dimensions")
    if disposition == "no_business_found" and output["identity_resolution"] == "resolved":
        errors.append("resolved_identity_conflicts_with_no_business_found")
    if disposition == "conflict_review" and contradiction_state != "unresolved":
        errors.append("conflict_review_requires_unresolved_contradiction")
    if disposition != deterministic_disposition(output):
        errors.append("research_disposition_conflicts_with_dimension_precedence")
    return errors


def deterministic_disposition(output: dict[str, Any]) -> str:
    """Apply safety-first precedence without changing any persisted workflow state."""

    if output["contradiction_state"] == "unresolved" or output["identity_resolution"] == "contradicted":
        return "conflict_review"
    if output["relationship"] == "none" and output["identity_resolution"] in {"ambiguous", "unresolved"}:
        return "no_business_found"
    if output["operating_status"] == "inactive" or output["relationship"] == "non_owner_role":
        return "no_qualifying_relationship"
    if output["relationship"] == "former_owner" and output["relationship_time"] == "ended_before_signal":
        return "no_qualifying_relationship"
    if (
        output["identity_resolution"] == "resolved"
        and output["relationship"] in {"current_owner", "successor"}
        and output["operating_status"] == "active"
    ):
        return "candidate_supported"
    return "needs_more_research"


def evaluate_output(
    output: dict[str, Any], expected: dict[str, str], allowed_source_ids: set[str], usage: TokenUsage
) -> EvaluationResult:
    validate(instance=output, schema=EVALUATION_SCHEMA_V2)
    errors = consistency_errors(output, allowed_source_ids)
    return EvaluationResult(
        provider_outcome="invalid" if errors else "completed",
        output=output,
        dimension_matches={dimension: output[dimension] == expected[dimension] for dimension in DIMENSIONS},
        consistency_errors=errors,
        usage=usage,
    )


def failed_evaluation(exc: Exception, usage: TokenUsage) -> EvaluationResult:
    """Keep failures observable and out of dimension-level classification metrics."""

    if isinstance(exc, AIProviderOutputError):
        outcome = exc.outcome
        reason = exc.reason
    elif isinstance(exc, (ValueError, TypeError, ValidationError)):
        outcome = "invalid"
        reason = None
    else:
        outcome = "failed"
        reason = None
    return EvaluationResult(
        provider_outcome=outcome,
        output=None,
        dimension_matches=None,
        consistency_errors=[],
        usage=usage,
        error_class=type(exc).__name__,
        error_reason=reason,
    )


def comparison_metrics(results: list[EvaluationResult]) -> dict[str, Any]:
    completed = [result for result in results if result.provider_outcome == "completed"]
    return {
        "calls": len(results),
        "provider_outcomes": {
            outcome: sum(result.provider_outcome == outcome for result in results)
            for outcome in ("completed", "incomplete", "refusal", "invalid", "failed")
        },
        "dimension_metrics": {
            dimension: {
                "evaluated": len(completed),
                "matches": (matches := sum(bool(result.dimension_matches and result.dimension_matches[dimension]) for result in completed)),
                "accuracy": matches / len(completed) if completed else None,
            }
            for dimension in DIMENSIONS
        },
        "tokens": {
            "input": sum(result.usage.input_tokens or 0 for result in results),
            "output": sum(result.usage.output_tokens or 0 for result in results),
            "total": sum(result.usage.total_tokens or 0 for result in results),
        },
    }


def serialize_result(result: EvaluationResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["usage"] = asdict(result.usage)
    return payload
