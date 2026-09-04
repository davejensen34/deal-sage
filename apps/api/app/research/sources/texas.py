from datetime import datetime, timezone
import json
from typing import Any
from urllib.parse import urlencode

import httpx

from app.research.landing import CuratedSubject
from app.research.sanitization import sanitize_external_mapping
from .base import SourceAdapter, SourceDefinition, SourceRecord


DATASET_ID = "9cir-efmm"
API_URL = f"https://data.texas.gov/resource/{DATASET_ID}.json"
SELECT_FIELDS = (
    "taxpayer_number,taxpayer_name,taxpayer_address,taxpayer_city,taxpayer_state,taxpayer_zip,"
    "taxpayer_county_code,taxpayer_organizational_type,record_type_code,responsibility_beginning_date,"
    "secretary_of_state_sos_or_coa_file_number,sos_charter_date,sos_status_date,sos_status_code,"
    "right_to_transact_business_code,current_exempt_reason_code,exempt_begin_date,_621111"
)


class TexasActiveFranchiseTaxpayersAdapter(SourceAdapter):
    definition = SourceDefinition(
        key="texas_active_franchise_taxpayers",
        name="Active Franchise Taxpayers",
        jurisdiction="Texas",
        source_type="government_open_dataset",
        publisher="Texas Comptroller of Public Accounts via Texas Open Data Portal",
        landing_url=f"https://data.texas.gov/d/{DATASET_ID}",
        api_url=API_URL,
        access_method="Public Socrata SODA API; bounded requests require no authentication",
        license="Texas public information; verify portal terms on contract change",
        expected_refresh="Published dataset metadata must be checked per run",
        role_value=(
            "Entity, tax-account, address, NAICS, SOS identifier, and "
            "right-to-transact corroboration only"
        ),
        limitations=(
            "Taxpayer status does not establish ownership.",
            "Organizational type does not identify a controlling person.",
            "The current portal field name `_621111` is labeled NAICS Code and must be contract-fingerprinted.",
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
            "$where": "taxpayer_state='TX'",
            "$order": "taxpayer_number ASC",
        }

    async def fetch_sample(self, limit: int = 50) -> list[SourceRecord]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=httpx.Timeout(20.0))
        try:
            response = await client.get(
                API_URL,
                params=self.query(limit),
                headers={
                    "User-Agent": "DealSage-Research/0.1 (+https://github.com/davejensen34/deal-sage)"
                },
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError("Texas source returned an unexpected payload")
            retrieved_at = datetime.now(timezone.utc)
            return [self._normalize_transport(record, retrieved_at) for record in payload]
        finally:
            if own_client:
                await client.aclose()

    @staticmethod
    def _normalize_transport(raw: Any, retrieved_at: datetime) -> SourceRecord:
        # The allowlist prevents newly added portal fields from silently entering
        # evidence before the source contract and privacy impact are reviewed.
        if (
            not isinstance(raw, dict)
            or not raw.get("taxpayer_number")
            or not raw.get("taxpayer_name")
        ):
            raise ValueError("Texas taxpayer record is missing required identity fields")
        policy = {field: True for field in SELECT_FIELDS.split(",")}
        selected = sanitize_external_mapping(raw, policy).data
        taxpayer_number = str(selected["taxpayer_number"])
        return SourceRecord(
            source_record_id=taxpayer_number,
            canonical_url=(
                "https://mycpa.cpa.state.tx.us/coa/coaSearchBtn?"
                f"SearchType=Taxpayer&InputType=TaxpayerNumber&Input={taxpayer_number}"
            ),
            retrieved_at=retrieved_at,
            raw=selected,
        )


def parse_curated_record(content: bytes) -> list[CuratedSubject]:
    raw = json.loads(content)
    if (
        not isinstance(raw, dict)
        or not raw.get("taxpayer_number")
        or not raw.get("taxpayer_name")
    ):
        raise ValueError("Texas taxpayer record is missing required identity fields")
    number = str(raw["taxpayer_number"])
    data = {
        "taxpayer_number": number,
        "legal_name": raw["taxpayer_name"],
        "address": raw.get("taxpayer_address"),
        "city": raw.get("taxpayer_city"),
        "state": raw.get("taxpayer_state"),
        "postal_code": raw.get("taxpayer_zip"),
        "organization_type": raw.get("taxpayer_organizational_type"),
        "sos_file_number": raw.get("secretary_of_state_sos_or_coa_file_number"),
        "right_to_transact_code": raw.get("right_to_transact_business_code"),
        "naics_code": raw.get("_621111"),
        "ownership_supported": False,
    }
    lineage = {
        "taxpayer_number": "$.taxpayer_number",
        "legal_name": "$.taxpayer_name",
        "address": "$.taxpayer_address",
        "city": "$.taxpayer_city",
        "state": "$.taxpayer_state",
        "postal_code": "$.taxpayer_zip",
        "organization_type": "$.taxpayer_organizational_type",
        "sos_file_number": "$.secretary_of_state_sos_or_coa_file_number",
        "right_to_transact_code": "$.right_to_transact_business_code",
        "naics_code": "$._621111",
        "ownership_supported": "$.__constant_false",
    }
    return [
        CuratedSubject(
            subject_key=f"tx-tax:{number}",
            subject_type="business",
            data=data,
            lineage=lineage,
        )
    ]


def public_query_url(limit: int = 50) -> str:
    return f"{API_URL}?{urlencode(TexasActiveFranchiseTaxpayersAdapter.query(limit))}"
