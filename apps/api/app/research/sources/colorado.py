from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
import httpx
from .base import SourceAdapter, SourceDefinition, SourceRecord


DATASET_ID = "4ykn-tg5h"
API_URL = f"https://data.colorado.gov/resource/{DATASET_ID}.json"
SELECT_FIELDS = (
    "entityid,entityname,entitytype,entitystatus,principalcity,principalstate,"
    "agentfirstname,agentmiddlename,agentlastname,agentsuffix,"
    "agentorganizationname,entityformdate"
)


class ColoradoBusinessEntitiesAdapter(SourceAdapter):
    definition = SourceDefinition(
        key="colorado_business_entities",
        name="Business Entities in Colorado",
        jurisdiction="Colorado",
        source_type="government_open_dataset",
        publisher="Colorado Department of State via Colorado Information Marketplace",
        landing_url="https://data.colorado.gov/d/4ykn-tg5h",
        api_url=API_URL,
        access_method="Public Socrata SODA API; no authentication for bounded requests",
        license="Public Domain",
        expected_refresh="Daily",
        role_value="Registered-agent evidence only in the bulk entity dataset; no owner/officer/director fields",
        limitations=(
            "A registered agent accepts service of process and must never be treated as an owner.",
            "The official Business Master File description says owners, officers, and directors are absent.",
            "A filing registry does not certify current operation, reputation, or beneficial ownership.",
        ),
        last_tested="2026-09-04",
    )

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client

    @staticmethod
    def query(limit: int) -> dict[str, str]:
        if not 1 <= limit <= 100:
            raise ValueError("Research samples must contain between 1 and 100 records")
        return {
            "$limit": str(limit),
            "$select": SELECT_FIELDS,
            "$where": "entitystatus='Good Standing' AND principalstate='CO' AND entitytype in('DLLC','DPC','DNC')",
            "$order": "entityid ASC",
        }

    async def fetch_sample(self, limit: int = 50) -> list[SourceRecord]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=httpx.Timeout(20.0))
        try:
            response = await client.get(API_URL, params=self.query(limit), headers={"User-Agent": "DealSage-Research/0.1 (+https://github.com/davejensen34/deal-sage)"})
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError("Colorado source returned an unexpected payload")
            retrieved_at = datetime.now(timezone.utc)
            return [self._normalize_transport(record, retrieved_at) for record in payload]
        finally:
            if own_client:
                await client.aclose()

    @staticmethod
    def _normalize_transport(raw: Any, retrieved_at: datetime) -> SourceRecord:
        # Keep only the explicitly selected fields so arbitrary source content cannot
        # expand the storage or instruction surface of a research run.
        if not isinstance(raw, dict) or not raw.get("entityid"):
            raise ValueError("Colorado source record is missing its entity identifier")
        selected = {field: raw.get(field) for field in SELECT_FIELDS.split(",")}
        entity_id = str(selected["entityid"])
        return SourceRecord(
            source_record_id=entity_id,
            canonical_url=f"https://www.sos.state.co.us/biz/BusinessEntityDetail.do?fileId={entity_id}",
            retrieved_at=retrieved_at,
            raw=selected,
        )


def public_query_url(limit: int = 50) -> str:
    return f"{API_URL}?{urlencode(ColoradoBusinessEntitiesAdapter.query(limit))}"
