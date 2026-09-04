from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any
from .sources.base import SourceRecord
from .sources.colorado import ColoradoBusinessEntitiesAdapter, public_query_url


@dataclass(frozen=True)
class RelationshipObservation:
    entity_id: str
    entity_type: str | None
    has_individual_agent: bool
    has_organization_agent: bool
    observed_role: str
    ownership_classification: str
    review_reason: str


def classify_record(record: SourceRecord) -> RelationshipObservation:
    raw = record.raw
    individual_agent = bool(raw.get("agentfirstname") or raw.get("agentlastname"))
    organization_agent = bool(raw.get("agentorganizationname"))
    # The dataset contract identifies these fields only as registered-agent data.
    # Address overlap or a natural-person name is not enough to upgrade the role.
    return RelationshipObservation(
        entity_id=record.source_record_id,
        entity_type=raw.get("entitytype"),
        has_individual_agent=individual_agent,
        has_organization_agent=organization_agent,
        observed_role="registered_agent" if individual_agent or organization_agent else "unknown",
        ownership_classification="unknown",
        review_reason="Registry supplies no owner/controller field; registered-agent evidence is non-ownership evidence.",
    )


def summarize(records: list[SourceRecord], latency_ms: int) -> dict[str, Any]:
    observations = [classify_record(record) for record in records]
    count = len(records)
    with_agent = sum(item.observed_role == "registered_agent" for item in observations)
    individuals = sum(item.has_individual_agent for item in observations)
    organizations = sum(item.has_organization_agent for item in observations)
    named = sum(bool(record.raw.get("entityname")) for record in records)
    dated = sum(bool(record.raw.get("entityformdate")) for record in records)
    return {
        "experiment": "Colorado owner-discovery falsification experiment",
        "status": "validated" if count == 50 else "partial",
        "sample_size": count,
        "query_url": public_query_url(count or 50),
        "selection": "First 50 entity IDs in ascending order among Colorado-principal domestic LLCs, professional corporations, and nonprofit corporations in Good Standing.",
        "review_method": "Conservative deterministic classification reviewed against the official dataset schema and Business Master File description. Agent fields are labeled registered_agent; ownership remains unknown.",
        "metrics": {
            "retrieval_success_percent": 100 if count else 0,
            "entity_name_coverage_percent": round(named / count * 100, 1) if count else 0,
            "formation_date_coverage_percent": round(dated / count * 100, 1) if count else 0,
            "registered_agent_evidence_percent": round(with_agent / count * 100, 1) if count else 0,
            "individual_agent_percent": round(individuals / count * 100, 1) if count else 0,
            "organization_agent_percent": round(organizations / count * 100, 1) if count else 0,
            "owner_controller_evidence_yield_percent": 0,
            "ownership_unknown_percent": 100 if count else 0,
            "retrieval_latency_ms": latency_ms,
            "marginal_api_cost_usd": 0,
        },
        "role_counts": {
            "registered_agent": with_agent,
            "owner": 0,
            "member": 0,
            "manager": 0,
            "officer": 0,
            "unknown_owner": count,
        },
        "recommendation": {
            "decision": "change",
            "summary": "Do not use Colorado's bulk business-entity dataset as an owner-discovery source.",
            "next_step": "Retain it for entity, address, status, and registered-agent evidence; evaluate a source or jurisdiction that explicitly exposes member, manager, officer, or owner roles.",
        },
        "observations": [asdict(item) for item in observations],
    }


async def run_colorado_experiment() -> tuple[list[SourceRecord], dict[str, Any]]:
    start = perf_counter()
    records = await ColoradoBusinessEntitiesAdapter().fetch_sample(50)
    return records, summarize(records, round((perf_counter() - start) * 1000))


def public_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Remove record-level observations before publishing an aggregate result."""
    return {key: value for key, value in result.items() if key != "observations"}
