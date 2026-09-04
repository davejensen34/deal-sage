# ADR-008: Evidence convergence and bounded public research

Status: accepted and implemented incrementally in Milestone 3.1. Current capability and validation boundaries are in `docs/project/current-state.md`.

## Context

Milestone 3 proved that state business sources can provide authoritative entity facts while signal-first public research can discover people and business clues without a predetermined company list. `CandidateMatch` is too late in the lifecycle to represent that work because it requires a resolved person, business, relationship, and transition signal.

Public web research and persistent acquisition also have different operational risk. Reading a public result for one bounded case does not require a reusable connector, while repeated collection must undergo source-specific access, automation, retention, privacy, and cost review.

## Decision

Use one `ResearchCase` for signal-first, business-first, and hybrid origins. Origin is provenance, not a separate pipeline. Evidence from business sources, transition sources, and public-web research converges through four explicit layers:

1. case-specific or connector-provided source evidence;
2. normalized claims derived from that evidence;
3. DealSage inferences supported by claim identifiers;
4. later analyst conclusions and workflow decisions.

Case-specific evidence retains a canonical URL, publisher and source type, publication/retrieval time, content hash, a small relevant excerpt where appropriate, extracted facts, and discovery provenance. It does not retain wholesale page content by default. Claims preserve semantic distinctions such as founder, owner, former owner, executive, employee, or registered agent. Inferences can be deterministic or model-assisted but are never source facts.

Use two explicit source modes:

- `case_specific_research` for bounded investigation through normal public access or an appropriate search/research provider;
- `persistent_connector` for systematic, repeated acquisition through an evaluated source contract.

This is an engineering and responsible-research policy, not a legal conclusion. Public visibility does not imply unrestricted crawling or republication, and bounded public research does not require a bespoke adapter or written agreement for every page.

All external response shapes require explicit allowlists. Unknown fields and capability-, session-, edit-, authentication-, or management-like fields are dropped in memory before any persistence or observability boundary. A defense-in-depth persistence guard rejects normalized spelling variants if unsafe fields reach it. Response-contract safety and source usefulness are evaluated separately; successful sanitation does not automatically promote a dynamic or case-specific source into a persistent connector.

## Consequences

- Research may begin before a person or business has been resolved.
- Search provider, model provider, frontier, budgets, and stopping behavior can attach to one shared case in later Milestone 3.1 slices.
- Cross-case claim and inference lineage is rejected.
- Model-assisted inference must record provider, model, and prompt version.
- Existing `CandidateMatch` remains the downstream reviewed opportunity object rather than being duplicated.
