# Milestone 3 — Multi-State Data Acquisition and Curation

Status: complete and validated (September 4, 2026).

## Progress

- Issue #20 established the primary-source registry and access decisions for Colorado, Utah, and Texas.
- Issue #22 implements the source-neutral raw-to-curated landing, signal-first unresolved subjects, replay, lineage, quarantine, and acquisition-run summaries.
- Issue #24 established the federated signal-first source portfolio and rejected recent vital records as a statewide discovery feed.
- Issue #26 implemented bounded Colorado and Texas source samples plus the purchase-free Utah BEL three-file contract fixture. Live Utah acquisition remained gated there until the later explicit authorization and delivery handled by Issue #32.
- Issue #28 adds analyst-facing aggregate source operations, including live/fixture distinctions and visible rejected or failed source states.
- Issue #30 persists deterministic signal-first outcomes so research can resolve to an existing business or terminate honestly without one.
- Issue #32 validates the authorized $5 Utah BEL delivery: three original CSV artifacts plus a deterministic joined package, 188 entities, 470 role assertions, clean repeat behavior, and aggregate-only publication.

## Goal

Build a trustworthy, replayable evidence supply chain for Colorado, Utah, and Texas that gives later deterministic and model-assisted research a curated foundation.

## Required scope

- Maintain a source registry with multiple candidate or validated sources for each state, including authority, role, access method, terms or automation constraints, refresh expectations, cost, fields, and known limitations.
- Maintain a federated signal-first portfolio for each state: discovery-capable obituary/probate/publisher sources plus downstream entity, tax, licensing, and filing corroboration. A statewide business download is not required.
- Support signal-first, business-first, and hybrid acquisition. Curated records may represent an unresolved person or transition signal before any business is known.
- Acquire bounded representative data from permitted sources without bypassing access controls, publisher rules, or reasonable rate limits.
- Separate immutable raw artifacts, normalized source records, validated evidence, and quarantined failures.
- Preserve source identity, retrieval timestamp, canonical URL or record identifier, content hash, parser/schema version, lineage, and transformation outcome.
- Normalize businesses, people, roles, addresses, and source assertions without treating registered agents or executives as owners.
- Treat entity search as downstream corroboration when a person or business clue is discovered, not as a discovery prerequisite.
- Support idempotent ingestion, deterministic deduplication, replay after parser changes, and visible source-change or parsing failures.
- Measure per-source and per-state retrieval success, field completeness, freshness, duplication, conflict, role coverage, latency, and marginal cost.
- Expose enough evidence and aggregate measures for an analyst to inspect what landed, what was rejected, and why.

## Definition of done

- Colorado, Utah, and Texas each have at least two documented sources across signal discovery and business corroboration with explicit purpose and limitations; at least one permitted source per state is exercised with a bounded representative sample.
- The raw-to-curated contract and retention boundary are documented and implemented behind source-neutral interfaces.
- Re-running the same acquisition is idempotent, and a stored raw artifact can be replayed through a newer parser without refetching it.
- Normalized facts retain field-level lineage to immutable source evidence; unsupported ownership remains unknown.
- A signal-first artifact can progress through person and business resolution or terminate honestly with no business found, without manufacturing a business record.
- Quarantine, source-contract drift, and partial failure are observable and do not silently publish facts.
- Automated tests, migration validation, and a local end-to-end demonstration pass without requiring an AI provider.
- Findings determine whether Milestone 4 has enough curated evidence to begin bounded model-assisted discovery.

## Explicitly deferred

Live OpenAI/Anthropic analysis, autonomous research planning, authoritative AI-written facts, opportunity scoring changes, watchlist automation, alerts, national coverage, and production-scale distributed ingestion.

## Closeout result

Colorado and Texas bounded live sources validate entity/status corroboration without ownership claims. Utah's bounded BEL delivery validates the three-file join and demonstrates stronger role evidence: 205 explicit `Owner`, 77 `Applicant`, and 188 `Registered Agent` rows across 188 entities. All 188 BUSINFO and 470 PRINCIPAL rows joined to known entities with no duplicate entity IDs, duplicate relationship tuples, orphan rows, or quarantine. Field completeness was 86.8%, the latest registration date was August 30, 2026, and the actual marginal cost was $5.

The delivered BUSINFO schema contained `Female Owned` and `Minority Owned` flags instead of the public example's information key/value fields. The importer recognizes that reviewed variant but retains those columns in private raw evidence rather than promoting them. Explicit owner-role rows become control-role candidates only; `ownership_validated` remains false until corroborating evidence and human review support it.

Milestone 3 therefore validates a replayable, provenance-preserving multi-state acquisition foundation. It does not establish comprehensive owner coverage, authorize recurring statewide purchases, or supply a live transition-signal feed.
