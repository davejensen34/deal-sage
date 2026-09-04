# Colorado owner-discovery falsification experiment

Status: validated on September 4, 2026.

## Question and decision

Can Colorado's official bulk business-entity data provide credible owner/controller evidence for a representative SMB research sample?

**Decision: change.** Keep this source for entity identity, status, address, formation date, and registered-agent evidence. Do not use it as an owner-discovery source. Evaluate a jurisdiction or permitted public source that explicitly publishes member, manager, officer, or owner roles.

## Source contract

- Publisher: Colorado Department of State via the Colorado Information Marketplace.
- Dataset: [Business Entities in Colorado](https://data.colorado.gov/d/4ykn-tg5h).
- Access: public Socrata SODA JSON API without authentication for this bounded request.
- License: public domain as published in the marketplace metadata.
- Expected refresh: daily.
- Official limitation: the [Business Master File description](https://www.sos.state.co.us/pubs/business/PDFFillable/BusinessMasterFile.pdf) says the file contains registered-agent fields and does not contain owners, officers, or directors.

The adapter requests only an explicit field allowlist, validates record identifiers, and preserves a canonical Colorado entity-detail URL and retrieval timestamp. Raw run output is stored locally under ignored `data/research/`; the repository contains only aggregate measures and fictional test fixtures.

## Method

The deterministic query selected the first 50 entity IDs in ascending order among good-standing entities with a Colorado principal state and entity types DLLC, DPC, or DNC. This stable ordering makes the test reproducible; it is a source-capability sample, not a statistically random estimate of all Colorado entities.

The role taxonomy is `owner`, `member`, `manager`, `officer`, `registered_agent`, and `unknown`. Records with individual or organization agent fields were classified only as `registered_agent`; all ownership classifications remained `unknown`. A person name, organization name, or address overlap was deliberately insufficient to infer ownership. No AI calls, candidate generation, or transition-signal generation occurred.

## Observed result

| Measure | Result |
|---|---:|
| Records retrieved | 50 |
| Retrieval success | 100% |
| Entity-name coverage | 100% |
| Formation-date coverage | 100% |
| Registered-agent evidence | 100% |
| Individual-agent records | 80% |
| Organization-agent records | 20% |
| Owner/controller evidence yield | 0% |
| Ownership unknown | 100% |
| Retrieval latency | 496 ms |
| Marginal API cost | $0 |

The source contract itself establishes the decisive precision boundary: a registered-agent field is not an owner field. Because no positive owner/controller assertions were available, owner-role precision and stale-owner rates are not measurable and must not be represented as zero. The correct result is zero usable owner coverage with 100% ownership ambiguity.

## Demonstration and follow-up

The Research page exposes the official source contract, exact public query, normalized role counts, aggregate quality measures, and decision without publishing record-level names. The next owner-discovery experiment should require explicit owner/controller roles before adapter implementation; Utah remains proposed pending current access, field, and terms verification.
