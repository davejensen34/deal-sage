# Milestone 3.1 validation assessment

This assessment records observed support as of September 4, 2026. It distinguishes implemented and tested behavior from live-source evidence; it is not a forecast or a claim that every research path has been exercised in production.

## Capability assessment

| Capability | Assessment | Evidence |
| --- | --- | --- |
| Common signal-first, business-first, and hybrid case model | Supported | `ResearchCase` accepts all three origins before a person or business is resolved; automated tests cover every direction. |
| Evidence → claim → inference → analyst conclusion separation | Supported | Separate durable models and cross-case guards are exercised by backend tests. |
| Minimal evidence and external-response sanitation | Supported | Content hashes and bounded excerpts are retained; allowlists and persistence guards reject capability/session fields. |
| Provider-neutral search and source candidates | Partially supported | The contract, budgets, provenance, failure handling, and fixture provider are tested. No live search provider is configured or exercised. |
| Obituary business-clue extraction | Partially supported | Fictional tests cover ownership, employment, executive, former-owner, sale, retirement, family-business, and ambiguous language. No live obituary corpus has been persisted. |
| Bounded frontier, planner, budgets, and stopping | Supported | Query/document/model/step/time/cost and attempt limits plus explicit stop reasons are tested deterministically. |
| Bidirectional identity resolution and aliases | Supported | Person-to-business, business-to-person, and hybrid tests reject name-only matching and preserve alias provenance. |
| Contradictions and evidence independence | Supported | Tests preserve conflicting claims and distinguish duplicate, syndicated, same-publisher, and independent evidence. |
| Explainable confidence and profile classification | Supported | Tests cover active owner, former owner, inactive business, ambiguous identity, contradictory ownership, non-independent suppression, and fact/estimate/inference labels. |
| Analyst research narrative | Supported | Authenticated API and rendered UI expose origin, hypothesis, activity, evidence, conflicts, confidence, stopping, and human conclusion without raw page bodies or agent logs. |
| Cross-strategy funnel metrics | Partially supported | Aggregate counts exist by origin and research layer without invented conversion rates; current local data contains no persisted convergence cases. |
| Live success and negative-case matrix | Partially supported | The approved seven-case CO/UT/TX cohort was executed within its call and cost ceilings. It exposed a conflated outcome taxonomy, two OpenAI incomplete outputs, and one internally inconsistent Anthropic classification; only 3 of 14 paths matched the pre-label. |
| Live OpenAI or Anthropic reasoning | Partially supported | Both providers processed the same public-evidence packets. Anthropic returned 7/7 schema-valid results on the corrected attempt; OpenAI returned 5/7. Evidence-bounded summaries were often useful, but comparative output quality is not yet acceptable. |

## Closeout decision

Milestone 3.1 remains active. Issue #53 executed the approved protocol and recorded the failures without changing pre-labels after seeing output. A version-two multidimensional evaluation contract is required before closeout. Utah BEL delivery remains a separate Milestone 3 dependency in Issue #32.
