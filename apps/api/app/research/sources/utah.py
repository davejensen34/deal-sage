from collections.abc import Mapping
import csv
from datetime import date
from io import BytesIO, StringIO
import json
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

from app.research.landing import CuratedSubject
from .base import SourceDefinition


CONTROL_ROLE_CANDIDATES = {
    "owner",
    "member",
    "manager",
    "managing member",
    "partner",
    "general partner",
}
REQUIRED_SHEETS = ("BUSENTITY", "BUSINFO", "PRINCIPAL")
MAX_ARCHIVE_ENTRY_BYTES = 5_000_000
EXPECTED_HEADERS = {
    "BUSENTITY": {
        "Entity Number", "Entity ID", "Entity Type", "License Type", "Business Name",
        "Address", "Address 2", "City", "State", "Zip Code", "Registration Date",
        "Expiration Date", "Home State", "License Status", "Status Reason",
        "Date Status Changed", "Last Renewal Date", "Applicant Name", "NAICS Code",
    },
    "PRINCIPAL": {
        "Entity ID", "Entity Type", "License Type", "Business Name", "Member Position",
        "Full name", "Address", "Address 2", "City", "State", "Zip Code",
    },
}
BUSINFO_HEADER_VARIANTS = (
    {"Entity ID", "Entity Type", "License Type", "Business Name", "Information Type", "Information"},
    {"Entity ID", "Entity Type", "License Type", "Business Name", "Female Owned", "Minority Owned"},
)

UTAH_BEL_DEFINITION = SourceDefinition(
    key="utah_business_entity_list",
    name="Businesses Registered in Utah / Business Entity List",
    jurisdiction="Utah",
    source_type="government_paid_dataset",
    publisher=(
        "Utah Department of Commerce, Division of Corporations and "
        "Commercial Code via Utah.gov"
    ),
    landing_url="https://secure.utah.gov/datarequest/businesses/index.html",
    api_url="",
    access_method=(
        "Paid list download; custom minimum $5 for first 200 records; "
        "no acquisition without approval"
    ),
    license="Utah public business-registration record under GRAMA; no separate redistribution license observed",
    expected_refresh="Official page reports data updated through the previous Tuesday",
    role_value=(
        "Entity plus reported officer, principal, partner, member-position, "
        "and registered-agent rows"
    ),
    limitations=(
        "Names and addresses only; no phone or email.",
        "Reported roles are evidence requiring validation, not authoritative beneficial ownership.",
        "Delivered CSV headers are contract-checked; observed BUSINFO demographic flags remain raw-only.",
    ),
    last_tested=None,
)


def canonical_bel_package_from_csv(files: Mapping[str, bytes]) -> bytes:
    """Convert the three delivered CSV lists to a deterministic parser package."""
    matched: dict[str, list[dict[str, str]]] = {}
    for filename, content in files.items():
        basename = PurePosixPath(filename).name.upper()
        sheet = next((name for name in REQUIRED_SHEETS if name in basename), None)
        if sheet is None:
            continue
        if sheet in matched:
            raise ValueError(f"Utah BEL delivery contains multiple {sheet} files")
        if len(content) > MAX_ARCHIVE_ENTRY_BYTES:
            raise ValueError(f"Utah BEL {sheet} file exceeds the bounded import limit")
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError(f"Utah BEL {sheet} file is not UTF-8 CSV") from error
        reader = csv.DictReader(StringIO(text))
        if not reader.fieldnames:
            raise ValueError(f"Utah BEL {sheet} file has no header")
        headers = {str(field).strip() for field in reader.fieldnames if field and str(field).strip()}
        if sheet == "BUSINFO":
            if headers not in BUSINFO_HEADER_VARIANTS:
                raise ValueError("Utah BEL BUSINFO headers differ from all reviewed variants")
        elif headers != EXPECTED_HEADERS[sheet]:
            raise ValueError(f"Utah BEL {sheet} headers differ from the reviewed contract")
        matched[sheet] = [
            {str(key).strip(): (value or "").strip() for key, value in row.items() if key and str(key).strip()}
            for row in reader
        ]

    missing = set(REQUIRED_SHEETS) - matched.keys()
    if missing:
        raise ValueError(f"Utah BEL delivery is missing: {', '.join(sorted(missing))}")
    return json.dumps(matched, sort_keys=True, separators=(",", ":")).encode()


def delivery_component_subject(sheet: str, content: bytes) -> list[CuratedSubject]:
    """Describe a delivered file without publishing any record-level values."""
    package = json.loads(canonical_bel_package_from_csv({f"{name}.csv": content if name == sheet else _empty_sheet(name) for name in REQUIRED_SHEETS}))
    rows = package[sheet]
    return [
        CuratedSubject(
            subject_key=f"ut-bel-delivery:{sheet.lower()}",
            subject_type="delivery_component",
            data={"sheet": sheet, "row_count": len(rows), "headers": sorted(rows[0]) if rows else []},
            lineage={},
        )
    ]


def _empty_sheet(sheet: str) -> bytes:
    if sheet == "BUSINFO":
        headers = sorted(BUSINFO_HEADER_VARIANTS[1])
    else:
        headers = sorted(EXPECTED_HEADERS[sheet])
    return (",".join(f'"{header}"' for header in headers) + "\n").encode()


def summarize_bel_package(content: bytes) -> dict[str, object]:
    """Calculate aggregate quality measures while names and addresses stay private."""
    package = json.loads(content)
    entities = package["BUSENTITY"]
    info = package["BUSINFO"]
    principals = package["PRINCIPAL"]
    entity_ids = [row.get("Entity ID", "") for row in entities]
    known_ids = set(entity_ids)
    role_counts: dict[str, int] = {}
    for row in principals:
        role = row.get("Member Position", "") or "Unknown"
        role_counts[role] = role_counts.get(role, 0) + 1
    relationship_keys = [
        (row.get("Entity ID"), row.get("Member Position"), row.get("Full name"))
        for row in principals
    ]
    observed_values = [value for row in entities + principals for value in row.values()]
    registration_dates = [
        date.fromisoformat(value)
        for row in entities
        if (value := row.get("Registration Date", ""))
    ]
    return {
        "entity_rows": len(entities),
        "business_info_rows": len(info),
        "principal_rows": len(principals),
        "entity_id_duplicates": len(entity_ids) - len(set(entity_ids)),
        "relationship_duplicates": len(relationship_keys) - len(set(relationship_keys)),
        "orphan_business_info_rows": sum(row.get("Entity ID") not in known_ids for row in info),
        "orphan_principal_rows": sum(row.get("Entity ID") not in known_ids for row in principals),
        "field_completeness_percent": round(sum(value not in (None, "") for value in observed_values) / len(observed_values) * 100, 1) if observed_values else 0,
        "role_counts": dict(sorted(role_counts.items())),
        "explicit_owner_role_assertions": role_counts.get("Owner", 0),
        "control_role_candidate_assertions": sum(
            count for role, count in role_counts.items() if role.casefold() in CONTROL_ROLE_CANDIDATES
        ),
        "latest_registration_date": max(registration_dates).isoformat() if registration_dates else None,
        "businfo_contract": "demographic_flags_raw_only" if "Female Owned" in (info[0] if info else {}) else "information_pairs_raw_only",
    }


def parse_bel_csv_archive(content: bytes) -> list[CuratedSubject]:
    """Parse a delivered ZIP while treating entry names and contents as untrusted."""
    try:
        with ZipFile(BytesIO(content)) as archive:
            if len(archive.infolist()) > 20:
                raise ValueError("Utah BEL archive contains too many entries")
            files = {}
            for entry in archive.infolist():
                if entry.is_dir():
                    continue
                if entry.flag_bits & 0x1:
                    raise ValueError("Encrypted Utah BEL archives are not supported")
                if entry.file_size > MAX_ARCHIVE_ENTRY_BYTES:
                    raise ValueError("Utah BEL archive entry exceeds the bounded import limit")
                files[entry.filename] = archive.read(entry)
    except BadZipFile as error:
        raise ValueError("Utah BEL delivery is not a valid ZIP archive") from error
    return parse_bel_package(canonical_bel_package_from_csv(files))


def parse_bel_package(content: bytes) -> list[CuratedSubject]:
    """Join the three documented BEL lists while retaining role uncertainty."""
    package = json.loads(content)
    entities = package.get("BUSENTITY", [])
    info = package.get("BUSINFO", [])
    principals = package.get("PRINCIPAL", [])
    if not isinstance(entities, list) or not isinstance(info, list) or not isinstance(principals, list):
        raise ValueError("Utah BEL package must contain three list-shaped sheets")
    by_id = {
        str(row.get("Entity ID")): row
        for row in entities
        if row.get("Entity ID") and row.get("Business Name")
    }
    if not by_id:
        raise ValueError("Utah BEL package contains no identified entities")

    subjects = []
    for entity_id, row in by_id.items():
        subjects.append(
            CuratedSubject(
                subject_key=f"ut-bel:{entity_id}",
                subject_type="business",
                data={
                    "entity_id": entity_id,
                    "registration_number": row.get("Entity Number"),
                    "legal_name": row.get("Business Name"),
                    "entity_type": row.get("Entity Type"),
                    "status": row.get("License Status"),
                    "city": row.get("City"),
                    "state": row.get("State"),
                    "naics_code": row.get("NAICS Code"),
                },
                lineage={
                    "entity_id": "$.BUSENTITY[].Entity ID",
                    "registration_number": "$.BUSENTITY[].Entity Number",
                    "legal_name": "$.BUSENTITY[].Business Name",
                    "entity_type": "$.BUSENTITY[].Entity Type",
                    "status": "$.BUSENTITY[].License Status",
                    "city": "$.BUSENTITY[].City",
                    "state": "$.BUSENTITY[].State",
                    "naics_code": "$.BUSENTITY[].NAICS Code",
                },
            )
        )

    for index, row in enumerate(principals):
        entity_id = str(row.get("Entity ID", ""))
        role = str(row.get("Member Position", "")).strip()
        name = str(row.get("Full name", "")).strip()
        if entity_id not in by_id or not role or not name:
            continue
        subjects.append(
            CuratedSubject(
                subject_key=f"ut-bel:{entity_id}:principal:{index}",
                subject_type="relationship_assertion",
                data={
                    "business_entity_id": entity_id,
                    "person_or_organization_name": name,
                    "reported_role": role,
                    "control_role_candidate": role.lower() in CONTROL_ROLE_CANDIDATES,
                    "ownership_validated": False,
                },
                lineage={
                    "business_entity_id": "$.PRINCIPAL[].Entity ID",
                    "person_or_organization_name": "$.PRINCIPAL[].Full name",
                    "reported_role": "$.PRINCIPAL[].Member Position",
                },
            )
        )
    # BUSINFO remains in the immutable delivery. Its open-ended information
    # types are not promoted until their semantics are observed and reviewed.
    return subjects
