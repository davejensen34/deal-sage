# ADR-007: Signal-first discovery and unresolved research subjects

Status: accepted. ADR-008 and Milestone 3.1 subsequently brought bounded model-assisted extraction and planning forward under the same deterministic controls; current behavior is in `docs/architecture/architecture.md`.

## Context

DealSage cannot depend on knowing a business name before discovery. State business registries are often lookup-oriented, incomplete for ownership, or too expensive to acquire comprehensively. The initial differentiating signal is a possible owner death, so a credible path may begin with a public death notice, memorial, or other transition event and only later discover whether the person controlled a business.

The existing business-first `ResearchTrail` remains useful for known-company research, but making it the only entry point would bias acquisition toward available business lists and exclude the core signal-first opportunity.

## Decision

Support three explicit discovery strategies: `signal_first`, `business_first`, and `hybrid`. Raw acquisition and curated observations may initially identify a transition signal or unresolved person without any business ID. Entity lookup is a downstream validation tool, not a prerequisite for discovery.

Use a strategy-neutral breadcrumb:

1. target/geography defined;
2. source evidence acquired;
3. transition signal or business clue extracted;
4. person identity resolved to the degree evidence permits;
5. candidate business discovered;
6. authoritative entity anchored;
7. person-to-business relationship validated;
8. candidate becomes analyst-review-ready.

Stages may be incomplete, branch, or terminate with “no business found” or “relationship unknown.” No stage may invent a business merely to satisfy the schema. Business-first trails can enter at candidate-business discovery and backfill earlier context; hybrid research can join independently acquired person/signal and business evidence.

Deterministic code owns artifact identity, lineage, state transitions, validation gates, and scores. Model-assisted extraction and research planning remain deferred to Milestone 4 and must operate on curated evidence.

## Consequences

- Milestone 3 landing records must support unresolved person, signal, business, and relationship subjects.
- State source portfolios need both population/discovery sources and authoritative lookup/corroboration sources; no single statewide business list is assumed.
- Funnel reporting must separate acquisition volume from resolved businesses and preserve negative outcomes.
- The existing business-first demo remains supported while its trail schema is generalized incrementally.
- Obituary and memorial sources still require source-specific access, terms, privacy, and responsible-research review before adapters are authorized.
