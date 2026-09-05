import csv
import json
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from app.research.experiment import classify_record, summarize
from app.research.ingestion import assert_safe_source_content, canonical_record_bytes
from app.research.sources.colorado import ColoradoBusinessEntitiesAdapter
from app.research.sources.texas import TexasActiveFranchiseTaxpayersAdapter, parse_curated_record as parse_texas
from app.research.sources.utah import (
    UTAH_BEL_DEFINITION,
    canonical_bel_package_from_csv,
    delivery_component_subject,
    parse_bel_csv_archive,
    parse_bel_package,
    summarize_bel_package,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures/colorado_records.json"


def csv_bytes(headers: list[str], row: dict[str, str] | None = None) -> bytes:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    if row:
        writer.writerow(row)
    return output.getvalue().encode()


def fixture_records() -> list[dict]:
    return json.loads(FIXTURE_PATH.read_text())


def test_colorado_query_is_bounded_and_reproducible():
    query = ColoradoBusinessEntitiesAdapter.query(50)
    assert query["$limit"] == "50"
    assert query["$order"] == "entityid ASC"
    with pytest.raises(ValueError):
        ColoradoBusinessEntitiesAdapter.query(101)


@pytest.mark.asyncio
async def test_adapter_normalizes_only_contract_fields():
    payload = [{**fixture_records()[0], "untrusted_extra": "ignore me"}]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        records = await ColoradoBusinessEntitiesAdapter(client).fetch_sample(1)
    assert records[0].source_record_id == "20240000001"
    assert "untrusted_extra" not in records[0].raw
    assert records[0].canonical_url.endswith("fileId=20240000001")


def test_registered_agent_is_never_classified_as_owner():
    now = datetime.now(timezone.utc)
    records = [ColoradoBusinessEntitiesAdapter._normalize_transport(raw, now) for raw in fixture_records()]
    observations = [classify_record(record) for record in records]
    assert {item.ownership_classification for item in observations} == {"unknown"}
    assert observations[0].observed_role == "registered_agent"
    assert observations[2].observed_role == "unknown"


def test_summary_reports_negative_owner_yield():
    now = datetime.now(timezone.utc)
    records = [ColoradoBusinessEntitiesAdapter._normalize_transport(raw, now) for raw in fixture_records()]
    result = summarize(records, 12)
    assert result["metrics"]["owner_controller_evidence_yield_percent"] == 0
    assert result["metrics"]["ownership_unknown_percent"] == 100
    assert result["recommendation"]["decision"] == "change"


def test_research_api_exposes_source_and_aggregate_result(client):
    sources = client.get("/api/research/sources")
    assert sources.status_code == 200
    assert sources.json()[0]["key"] == "colorado_business_entities"
    result = client.get("/api/research/experiments/colorado-owner-discovery")
    assert result.status_code == 200
    assert "observations" not in result.json()
    samples = client.get("/api/research/experiments/milestone3-source-samples")
    assert samples.status_code == 200
    assert samples.json()["contains_record_level_data"] is False
    assert "taxpayer_name" not in str(samples.json())


@pytest.mark.asyncio
async def test_texas_adapter_is_bounded_and_ignores_uncontracted_fields():
    payload=json.loads((Path(__file__).parent/"fixtures/texas_taxpayer.json").read_text())
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request:httpx.Response(200,json=[{**payload,"untrusted_extra":"ignore"}]))) as client:
        records=await TexasActiveFranchiseTaxpayersAdapter(client).fetch_sample(1)
    assert records[0].source_record_id == "32099999999"
    assert "untrusted_extra" not in records[0].raw
    assert TexasActiveFranchiseTaxpayersAdapter.query(1)["$where"] == "taxpayer_state='TX'"
    with pytest.raises(ValueError): TexasActiveFranchiseTaxpayersAdapter.query(101)
    assert len(TexasActiveFranchiseTaxpayersAdapter.definition.contract_fingerprint) == 64


def test_texas_tax_status_never_claims_ownership():
    content=(Path(__file__).parent/"fixtures/texas_taxpayer.json").read_bytes()
    subject=parse_texas(content)[0]
    assert subject.subject_type == "business"
    assert subject.data["right_to_transact_code"] == "A"
    assert subject.data["ownership_supported"] is False


def test_utah_bel_join_preserves_role_without_validating_ownership():
    content=(Path(__file__).parent/"fixtures/utah_bel_package.json").read_bytes()
    subjects=parse_bel_package(content)
    member=next(item for item in subjects if item.data.get("reported_role")=="Member")
    agent=next(item for item in subjects if item.data.get("reported_role")=="Registered Agent")
    assert member.data["control_role_candidate"] is True
    assert member.data["ownership_validated"] is False
    assert agent.data["control_role_candidate"] is False
    assert len(UTAH_BEL_DEFINITION.contract_fingerprint) == 64


def test_utah_delivery_csvs_join_from_the_actual_three_file_contract():
    entity_headers = [
        "Entity Number", "Entity ID", "Entity Type", "License Type", "Business Name",
        "Address", "Address 2", "City", "State", "Zip Code", "Registration Date",
        "Expiration Date", "Home State", "License Status", "Status Reason",
        "Date Status Changed", "Last Renewal Date", "Applicant Name", "NAICS Code",
    ]
    info_headers = [
        "Entity ID", "Entity Type", "License Type", "Business Name", "Female Owned", "Minority Owned",
    ]
    principal_headers = [
        "Entity ID", "Entity Type", "License Type", "Business Name", "Member Position",
        "Full name", "Address", "Address 2", "City", "State", "Zip Code",
    ]
    files = {
        "order_BUSENTITY.csv": csv_bytes(
            entity_headers,
            {"Entity Number": "9999999-0160", "Entity ID": "9999999", "Entity Type": "Domestic Limited Liability Company", "Business Name": "Fictional Wasatch Tool LLC", "City": "Provo", "State": "UT", "License Status": "Active", "NAICS Code": "332710", "Registration Date": "2026-08-15"},
        ),
        "order_BUSINFO.csv": csv_bytes(
            info_headers,
            {"Entity ID": "9999999", "Entity Type": "LLC", "Business Name": "Fictional Wasatch Tool LLC", "Female Owned": "No", "Minority Owned": "No"},
        ),
        "order_PRINCIPAL.csv": csv_bytes(
            principal_headers,
            {"Entity ID": "9999999", "Entity Type": "LLC", "Business Name": "Fictional Wasatch Tool LLC", "Member Position": "Member", "Full name": "Jordan Example", "City": "Provo", "State": "UT"},
        ),
    }
    package = canonical_bel_package_from_csv(files)
    subjects = parse_bel_package(package)
    assert [subject.subject_type for subject in subjects] == [
        "business",
        "relationship_assertion",
    ]
    assert subjects[1].data["ownership_validated"] is False
    assert delivery_component_subject("BUSINFO", files["order_BUSINFO.csv"])[0].data["row_count"] == 1
    assert summarize_bel_package(package) == {
        "entity_rows": 1,
        "business_info_rows": 1,
        "principal_rows": 1,
        "entity_id_duplicates": 0,
        "relationship_duplicates": 0,
        "orphan_business_info_rows": 0,
        "orphan_principal_rows": 0,
        "field_completeness_percent": 53.3,
        "role_counts": {"Member": 1},
        "explicit_owner_role_assertions": 0,
        "control_role_candidate_assertions": 1,
        "latest_registration_date": "2026-08-15",
        "businfo_contract": "demographic_flags_raw_only",
    }

    archive_bytes = BytesIO()
    with ZipFile(archive_bytes, "w") as archive:
        for filename, content in files.items():
            archive.writestr(filename, content)
    assert len(parse_bel_csv_archive(archive_bytes.getvalue())) == 2


def test_utah_delivery_rejects_missing_or_duplicate_contract_files():
    entity_headers = [
        "Entity Number", "Entity ID", "Entity Type", "License Type", "Business Name",
        "Address", "Address 2", "City", "State", "Zip Code", "Registration Date",
        "Expiration Date", "Home State", "License Status", "Status Reason",
        "Date Status Changed", "Last Renewal Date", "Applicant Name", "NAICS Code",
    ]
    entity_file = csv_bytes(entity_headers)
    with pytest.raises(ValueError, match="missing"):
        canonical_bel_package_from_csv({"BUSENTITY.csv": entity_file})
    with pytest.raises(ValueError, match="multiple BUSENTITY"):
        canonical_bel_package_from_csv(
            {
                "one_BUSENTITY.csv": entity_file,
                "two_BUSENTITY.csv": entity_file,
            }
        )


def test_utah_delivery_rejects_unreviewed_header_drift():
    with pytest.raises(ValueError, match="headers differ"):
        canonical_bel_package_from_csv({"BUSINFO.csv": b"Entity ID,Business Name,Unexpected\n1,Example,value\n"})


def test_utah_explicit_owner_role_is_a_candidate_not_validated_ownership():
    package = {
        "BUSENTITY": [{"Entity ID": "1", "Business Name": "Fictional Owner Test LLC"}],
        "BUSINFO": [],
        "PRINCIPAL": [{"Entity ID": "1", "Member Position": "Owner", "Full name": "Taylor Example"}],
    }

    relationship = parse_bel_package(json.dumps(package).encode())[1]

    assert relationship.data["reported_role"] == "Owner"
    assert relationship.data["control_role_candidate"] is True
    assert relationship.data["ownership_validated"] is False


def test_canonical_evidence_is_stable_and_rejects_sensitive_source_fields():
    retrieved_at = datetime.now(timezone.utc)
    first = ColoradoBusinessEntitiesAdapter._normalize_transport(fixture_records()[0], retrieved_at)
    reordered = ColoradoBusinessEntitiesAdapter._normalize_transport(
        dict(reversed(list(fixture_records()[0].items()))), retrieved_at
    )
    assert canonical_record_bytes(first) == canonical_record_bytes(reordered)

    with pytest.raises(ValueError, match="Forbidden source field"):
        assert_safe_source_content({"public": {"edit_token": "must-not-land"}})
