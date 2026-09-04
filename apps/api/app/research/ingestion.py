from dataclasses import dataclass
import json
from time import perf_counter
from typing import Any

from app.research.landing import EvidenceLanding, LandingEnvelope, Parser
from app.research.sources.base import SourceAdapter, SourceRecord


# These fields have appeared in otherwise public discovery responses and can
# behave like credentials. Reject the whole record before raw evidence storage;
# silently redacting it would make the retained artifact an ambiguous source.
FORBIDDEN_SOURCE_FIELDS = frozenset(
    {
        "access_token",
        "api_key",
        "client_secret",
        "creation_session_id",
        "edit_token",
        "password",
        "refresh_token",
    }
)


@dataclass(frozen=True)
class SampleResult:
    source_key: str
    jurisdiction: str
    requested: int
    retrieved: int
    curated: int
    quarantined: int
    duplicate_artifacts: int
    field_completeness_percent: float
    relationship_assertions: int
    ownership_supported_assertions: int
    retrieval_latency_ms: int
    marginal_cost_usd: float

    def public_summary(self) -> dict[str, Any]:
        """Return aggregate-only measures safe to commit or expose to analysts."""
        return {
            "source_key": self.source_key,
            "jurisdiction": self.jurisdiction,
            "requested": self.requested,
            "retrieved": self.retrieved,
            "curated": self.curated,
            "quarantined": self.quarantined,
            "duplicate_artifacts": self.duplicate_artifacts,
            "field_completeness_percent": self.field_completeness_percent,
            "relationship_assertions": self.relationship_assertions,
            "ownership_supported_assertions": self.ownership_supported_assertions,
            "freshness": {
                "status": "not_measurable_from_record",
                "reason": "Source records do not expose a reliable last-updated timestamp; monitor dataset metadata separately.",
            },
            "retrieval_success_percent": round(self.retrieved / self.requested * 100, 1),
            "retrieval_latency_ms": self.retrieval_latency_ms,
            "marginal_cost_usd": self.marginal_cost_usd,
        }


def canonical_record_bytes(record: SourceRecord) -> bytes:
    """Freeze one contracted source record into deterministic evidence bytes."""
    assert_safe_source_content(record.raw)
    return json.dumps(record.raw, sort_keys=True, separators=(",", ":")).encode()


def assert_safe_source_content(value: Any, path: str = "$") -> None:
    """Reject credential-like keys recursively before evidence is persisted."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = str(key).lower()
            if normalized_key in FORBIDDEN_SOURCE_FIELDS:
                raise ValueError(f"Forbidden source field at {path}.{key}")
            assert_safe_source_content(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_safe_source_content(child, f"{path}[{index}]")


async def acquire_and_land_sample(
    adapter: SourceAdapter,
    landing: EvidenceLanding,
    parser: Parser,
    *,
    limit: int,
    parser_version: str,
    schema_version: str,
    discovery_strategy: str = "business_first",
    marginal_cost_usd: float = 0,
) -> SampleResult:
    """Fetch and land a bounded sample without exposing record-level data."""
    run = landing.start_run(
        adapter.definition.key,
        adapter.definition.jurisdiction,
        discovery_strategy,
        adapter.definition.contract_fingerprint,
    )
    started = perf_counter()
    try:
        records = await adapter.fetch_sample(limit)
    except Exception as error:
        landing.fail_run(run, error)
        raise
    retrieval_latency_ms = round((perf_counter() - started) * 1000)
    curated = 0
    quarantined = 0
    relationship_assertions = 0
    ownership_supported_assertions = 0
    seen_hashes: set[bytes] = set()

    for record in records:
        content = canonical_record_bytes(record)
        seen_hashes.add(content)
        outcomes = landing.land(
            run,
            LandingEnvelope(
                source_key=adapter.definition.key,
                source_record_id=record.source_record_id,
                canonical_url=record.canonical_url,
                retrieved_at=record.retrieved_at,
                media_type="application/json",
                contract_fingerprint=adapter.definition.contract_fingerprint,
                request_metadata={"bounded_sample": True, "limit": limit},
                content=content,
            ),
            parser,
            parser_version,
            schema_version,
        )
        curated += sum(outcome.status == "curated" for outcome in outcomes)
        quarantined += sum(outcome.status == "quarantined" for outcome in outcomes)
        relationship_assertions += sum(
            outcome.subject_type == "relationship_assertion" for outcome in outcomes
        )
        ownership_supported_assertions += sum(
            outcome.normalized_data.get("ownership_supported") is True
            or outcome.normalized_data.get("ownership_validated") is True
            for outcome in outcomes
        )

    # Duplicate transport records are measured within this bounded run. Storage
    # deduplication across earlier runs remains represented by RunArtifact links.
    duplicate_count = len(records) - len(seen_hashes)
    observed_fields = sum(len(record.raw) for record in records)
    populated_fields = sum(
        value not in (None, "") for record in records for value in record.raw.values()
    )
    return SampleResult(
        source_key=adapter.definition.key,
        jurisdiction=adapter.definition.jurisdiction,
        requested=limit,
        retrieved=len(records),
        curated=curated,
        quarantined=quarantined,
        duplicate_artifacts=duplicate_count,
        field_completeness_percent=(
            round(populated_fields / observed_fields * 100, 1) if observed_fields else 0
        ),
        relationship_assertions=relationship_assertions,
        ownership_supported_assertions=ownership_supported_assertions,
        retrieval_latency_ms=retrieval_latency_ms,
        marginal_cost_usd=marginal_cost_usd,
    )
