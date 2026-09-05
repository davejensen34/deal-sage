# Utah BEL bounded-delivery experiment

Status: validated on September 4, 2026 through Issue #32. This report contains aggregate measures only; the delivered record-level files remain in ignored private evidence storage.

## Question and access decision

Determine whether the Utah.gov Business Entity List can provide replayable entity and owner/controller-role evidence for a bounded SMB sample. The user explicitly authorized the minimum $5 custom purchase. No full-list purchase, scraping, recurring acquisition, or record-level publication was authorized.

Utah describes its business-registration information as public under GRAMA and offers the BEL through its paid list service. The order and delivery did not provide a separate redistribution license. DealSage therefore retains the delivered names and addresses privately, publishes aggregates only, and requires a new review before any repeat purchase or broader use.

Official references:

- https://secure.utah.gov/datarequest/index.html
- https://secure.utah.gov/datarequest/businesses/index.html
- https://secure.utah.gov/datarequest/businesses/listExample.html
- https://commerce.utah.gov/2021/10/25/public-disclosure-of-information/

## Delivered contract

The delivery contained three separate CSV files:

- BUSENTITY: 188 entity rows;
- BUSINFO: 188 rows;
- PRINCIPAL: 470 rows.

BUSENTITY and PRINCIPAL matched the published logical contract. BUSINFO instead contained `Female Owned` and `Minority Owned` columns. The importer treats this as an explicitly reviewed schema variant, retains the flags only in raw private evidence, and does not promote them into curated business facts.

Each original CSV lands as its own immutable, content-addressed artifact. A fourth deterministic canonical package supports the cross-file join and replay. The committed result contains no names, addresses, entity identifiers, or raw rows.

## Observed result

| Measure | Result |
| --- | ---: |
| Entity retrieval and ingestion | 188/188 (100%) |
| BUSINFO rows joined | 188/188 |
| PRINCIPAL rows joined | 470/470 |
| Curated businesses | 188 |
| Relationship assertions | 470 |
| Explicit `Owner` role assertions | 205 |
| `Applicant` role assertions | 77 |
| `Registered Agent` role assertions | 188 |
| Duplicate entity IDs | 0 |
| Duplicate entity/role/name tuples | 0 |
| Orphan BUSINFO or PRINCIPAL rows | 0 |
| Quarantined results | 0 |
| Delivered-field completeness | 86.8% |
| Latest registration date | August 30, 2026 |
| Marginal cost | $5 |

An identical second ingestion added no raw artifacts and returned the existing curated results, confirming idempotent repeat behavior. Generic landing tests also verify replay under a new parser version without refetching source evidence.

## Decision

**Validate for bounded entity and owner-role candidate evidence.** The delivery materially improves on Colorado and Texas for relationship discovery because it contains an explicit `Owner` label. That label is still a source assertion: the importer marks it as a control-role candidate while keeping `ownership_validated=false`. Applicant and registered-agent roles never imply ownership.

The experiment satisfies Milestone 3's Utah live-source requirement and supports closing the milestone. It does not prove beneficial ownership, comprehensive coverage, current control, or permission for recurring statewide acquisition.
