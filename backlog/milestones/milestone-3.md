# Milestone 3 — Multi-State Data Acquisition and Curation

Status: paused, not closed. Issues #20–#30 are complete; Issue #32 is waiting for the authorized Utah BEL delivery on the preserved `feature/32-utah-live-sample` branch.

## Progress

- Issue #20 established the primary-source registry and access decisions for Colorado, Utah, and Texas.
- Issue #22 implements the source-neutral raw-to-curated landing, signal-first unresolved subjects, replay, lineage, quarantine, and acquisition-run summaries.
- Issue #24 established the federated signal-first source portfolio and rejected recent vital records as a statewide discovery feed.
- Issue #26 implements bounded Colorado and Texas source samples plus the purchase-free Utah BEL three-file contract fixture. A live Utah sample remains gated by explicit cost approval.
- Issue #28 adds analyst-facing aggregate source operations, including live/fixture distinctions and visible rejected or failed source states.
- Issue #30 persists deterministic signal-first outcomes so research can resolve to an existing business or terminate honestly without one.

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
