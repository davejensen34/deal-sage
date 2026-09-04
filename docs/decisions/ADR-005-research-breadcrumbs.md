# ADR-005: Evidence-backed research breadcrumbs

## Context

Milestone 2 demonstrated that an authoritative registry can identify an entity while exposing no owner/controller truth. DealSage needs to build confidence progressively without silently merging businesses, websites, and people.

## Decision

Model a `ResearchTrail` for each researched business and ordered `ResearchStage` observations for target fit, discovery, authoritative anchoring, business validation, web validation, person discovery, relationship validation, and owner research readiness. Each stage keeps its own status, confidence, evidence references, source, support, contradictions, and gaps.

Owner readiness is a deterministic spending gate, not an ownership fact. It requires an explicit controlling-role type, at least 75% owner/business confidence, and validated business, web, and relationship stages. Registered agent, officer, president, founder, and former owner do not qualify by title alone.

## Consequences

Funnel counts come from persisted validated stages rather than invented conversion assumptions. Transition-signal discovery can later begin only for justified people, while analysts can still inspect incomplete or contradictory paths. AI may help interpret deep unstructured evidence but does not calculate readiness or mutate stage state autonomously.
