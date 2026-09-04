# Milestone 3.1 — Evidence Convergence and Dynamic Discovery

Status: in progress in GitHub Milestone 3.1. Milestone 3 remains paused—not closed—while its authorized Utah BEL delivery is pending in Issue #32.

## Goal

Enable DealSage to enter research from a transition signal, business, or both; discover and preserve case-specific public evidence; extract semantically precise claims; ask bounded next questions; and converge on an auditable research conclusion without requiring a predetermined company list.

## Product principles

- `signal_first`, `business_first`, and `hybrid` describe case origin, not separate resolution architectures.
- Source evidence, normalized claims, DealSage inferences, and analyst conclusions remain distinct and traceable.
- Case-specific public research does not require a reusable adapter for every page. Persistent connectors require stronger source onboarding and access review.
- Search and model reasoning are separate provider-neutral capabilities. An LLM is never assumed to have web access.
- Dynamic research is bounded by queries, documents, model use, steps, time, and cost; stopping is explicit.
- Negative and contradictory evidence is retained. A transition signal never implies that a business is for sale.

## Planned slices

1. Research case, evidence, claim, and inference foundation.
2. External-response sanitation and case-specific public-research policy.
3. Provider-neutral search and dynamic source candidates.
4. Obituary business-clue extraction with precise relationship semantics.
5. Research frontier, bounded planner, budgets, and stopping criteria.
6. Bidirectional person/business resolution, aliases, contradictions, and evidence independence.
7. Explainable confidence convergence and operating-status/profile evidence.
8. Analyst research narrative, funnel/cross-strategy metrics, and live validation.

Issue boundaries may change as implementation evidence emerges; GitHub Issues remain the actionable work record.

## Progress

- Issue #33 established the shared unresolved research case and evidence→claim→inference traceability spine.
- Issue #35 implements reusable nested allowlisting, recursive capability-field removal, and defense-in-depth persistence rejection while keeping source safety distinct from usefulness.
- Issue #37 adds provider-neutral bounded search provenance and dynamic source candidates that never become evidence or persistent connectors automatically.
- Issue #39 adds a provider-neutral obituary business-clue contract and deterministic baseline that preserves explicit relationship, former-owner, sale, and retirement language as source-backed claims without inferring current ownership.
- Issue #41 adds durable frontier questions and deterministic bounded planning with reconstructable action/model provenance, attempt limits, research budgets, and explicit stopping reasons.

## Definition of done

- Business, transition, and public-web evidence converge through one common case-resolution model.
- Broad signal-first research can produce business clues and deterministic state/entity corroboration while business-first and hybrid entry remain supported.
- Case-specific research, source candidates, known sources, and persistent adapters are structurally and operationally distinct.
- External responses are allowlisted before persistence; capability/session/edit fields cannot enter evidence, logs, fixtures, APIs, or telemetry accidentally.
- Search providers and model providers are replaceable, separately modeled, bounded, and actually exercised where configured.
- Research frontier items, queries, steps, budgets, stop reasons, and provider/cost provenance are reconstructable.
- Claims preserve relationship language, dates, source authority/directness, uncertainty, and fact/estimate/inference boundaries.
- Resolution handles aliases, geography/timeline evidence, contradictions, negative outcomes, and likely duplicate/syndicated evidence without name-only merging.
- Confidence remains explainable and keeps business identity, owner relationship, transition identity, and overall opportunity concepts distinct.
- Analysts can understand case origin, searches, evidence, conflicts, confidence changes, stopping reason, and opportunity hypothesis without reading raw agent logs.
- Actual signal-first and cross-strategy funnel metrics are captured without invented conversion rates.
- Live validation includes success, former-owner, inactive-business, ambiguous-identity, contradictory-ownership, and business-first cases.
- Automated tests, migration validation, rendered UX validation, GitHub state, architecture, backlog, roadmap, and current state are reconciled.

## Explicitly excluded

Nationwide unrestricted crawling, dozens of bespoke obituary scrapers, full AI usage-policy governance, CRM/outreach automation, autonomous contact workflows, distributed enterprise infrastructure, sophisticated trained entity-resolution models, and multi-agent architecture for its own sake.
