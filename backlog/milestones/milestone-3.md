# Milestone 3 — Multi-State Data Acquisition and Curation

Status: ready for kickoff; implementation not started.

## Goal

Build a trustworthy, replayable evidence supply chain for Colorado, Utah, and Texas that gives later deterministic and model-assisted research a curated foundation.

## Required scope

- Maintain a source registry with multiple candidate or validated sources for each state, including authority, role, access method, terms or automation constraints, refresh expectations, cost, fields, and known limitations.
- Acquire bounded representative data from permitted sources without bypassing access controls, publisher rules, or reasonable rate limits.
- Separate immutable raw artifacts, normalized source records, validated evidence, and quarantined failures.
- Preserve source identity, retrieval timestamp, canonical URL or record identifier, content hash, parser/schema version, lineage, and transformation outcome.
- Normalize businesses, people, roles, addresses, and source assertions without treating registered agents or executives as owners.
- Support idempotent ingestion, deterministic deduplication, replay after parser changes, and visible source-change or parsing failures.
- Measure per-source and per-state retrieval success, field completeness, freshness, duplication, conflict, role coverage, latency, and marginal cost.
- Expose enough evidence and aggregate measures for an analyst to inspect what landed, what was rejected, and why.

## Definition of done

- Colorado, Utah, and Texas each have at least two documented sources with explicit purpose and limitations; at least one permitted source per state is exercised with a bounded representative sample.
- The raw-to-curated contract and retention boundary are documented and implemented behind source-neutral interfaces.
- Re-running the same acquisition is idempotent, and a stored raw artifact can be replayed through a newer parser without refetching it.
- Normalized facts retain field-level lineage to immutable source evidence; unsupported ownership remains unknown.
- Quarantine, source-contract drift, and partial failure are observable and do not silently publish facts.
- Automated tests, migration validation, and a local end-to-end demonstration pass without requiring an AI provider.
- Findings determine whether Milestone 4 has enough curated evidence to begin bounded model-assisted discovery.

## Explicitly deferred

Live OpenAI/Anthropic analysis, autonomous research planning, authoritative AI-written facts, opportunity scoring changes, watchlist automation, alerts, national coverage, and production-scale distributed ingestion.
