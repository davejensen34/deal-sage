import json
from app.research.landing import CuratedSubject
from .base import SourceDefinition

CONTROL_ROLE_CANDIDATES={"member","manager","managing member","partner","general partner"}
UTAH_BEL_DEFINITION=SourceDefinition(key="utah_business_entity_list",name="Businesses Registered in Utah / Business Entity List",jurisdiction="Utah",source_type="government_paid_dataset",publisher="Utah Department of Commerce, Division of Corporations and Commercial Code via Utah.gov",landing_url="https://secure.utah.gov/datarequest/businesses/index.html",api_url="",access_method="Paid list download; custom minimum $5 for first 200 records; no acquisition without approval",license="Public record under GRAMA; purchase and reuse terms require confirmation",expected_refresh="Official page reports data updated through the previous Tuesday",role_value="Entity plus reported officer, principal, partner, member-position, and registered-agent rows",limitations=("Names and addresses only; no phone or email.","Reported roles are evidence requiring validation, not authoritative beneficial ownership.","Current delivery format must be verified against the documented three-sheet example after purchase."),last_tested=None)


def parse_bel_package(content:bytes)->list[CuratedSubject]:
    """Join the three documented BEL sheets while retaining role uncertainty."""
    package=json.loads(content)
    entities=package.get("BUSENTITY",[]); info=package.get("BUSINFO",[]); principals=package.get("PRINCIPAL",[])
    if not isinstance(entities,list) or not isinstance(info,list) or not isinstance(principals,list): raise ValueError("Utah BEL package must contain three list-shaped sheets")
    by_id={str(row.get("Entity ID")):row for row in entities if row.get("Entity ID") and row.get("Business Name")}
    if not by_id: raise ValueError("Utah BEL package contains no identified entities")
    subjects=[]
    for entity_id,row in by_id.items():
        subjects.append(CuratedSubject(subject_key=f"ut-bel:{entity_id}",subject_type="business",data={"entity_id":entity_id,"registration_number":row.get("Entity Number"),"legal_name":row.get("Business Name"),"entity_type":row.get("Entity Type"),"status":row.get("License Status"),"city":row.get("City"),"state":row.get("State"),"naics_code":row.get("NAICS Code")},lineage={"entity_id":"$.BUSENTITY[].Entity ID","registration_number":"$.BUSENTITY[].Entity Number","legal_name":"$.BUSENTITY[].Business Name","entity_type":"$.BUSENTITY[].Entity Type","status":"$.BUSENTITY[].License Status","city":"$.BUSENTITY[].City","state":"$.BUSENTITY[].State","naics_code":"$.BUSENTITY[].NAICS Code"}))
    for index,row in enumerate(principals):
        entity_id=str(row.get("Entity ID","")); role=str(row.get("Member Position","")).strip(); name=str(row.get("Full name","")).strip()
        if entity_id not in by_id or not role or not name: continue
        subjects.append(CuratedSubject(subject_key=f"ut-bel:{entity_id}:principal:{index}",subject_type="relationship_assertion",data={"business_entity_id":entity_id,"person_or_organization_name":name,"reported_role":role,"control_role_candidate":role.lower() in CONTROL_ROLE_CANDIDATES,"ownership_validated":False},lineage={"business_entity_id":"$.PRINCIPAL[].Entity ID","person_or_organization_name":"$.PRINCIPAL[].Full name","reported_role":"$.PRINCIPAL[].Member Position"}))
    # BUSINFO is retained in the raw package; unsupported types are intentionally
    # not promoted until their documented semantics are mapped.
    return subjects
