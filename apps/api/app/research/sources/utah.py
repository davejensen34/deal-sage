from collections.abc import Mapping
import csv
from io import BytesIO, StringIO
import json
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

from app.research.landing import CuratedSubject
from .base import SourceDefinition


CONTROL_ROLE_CANDIDATES = {
    "member",
    "manager",
    "managing member",
    "partner",
    "general partner",
}
REQUIRED_SHEETS = ("BUSENTITY", "BUSINFO", "PRINCIPAL")
MAX_ARCHIVE_ENTRY_BYTES = 5_000_000

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
    license="Public record under GRAMA; purchase and reuse terms require confirmation",
    expected_refresh="Official page reports data updated through the previous Tuesday",
    role_value=(
        "Entity plus reported officer, principal, partner, member-position, "
        "and registered-agent rows"
    ),
    limitations=(
        "Names and addresses only; no phone or email.",
        "Reported roles are evidence requiring validation, not authoritative beneficial ownership.",
        "Delivered archive and CSV headers must match the documented three-list contract.",
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
        matched[sheet] = [
            {str(key).strip(): (value or "").strip() for key, value in row.items()}
            for row in reader
        ]

    missing = set(REQUIRED_SHEETS) - matched.keys()
    if missing:
        raise ValueError(f"Utah BEL delivery is missing: {', '.join(sorted(missing))}")
    return json.dumps(matched, sort_keys=True, separators=(",", ":")).encode()


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
