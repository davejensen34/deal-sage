# Product backlog

This directory preserves roadmap sequencing, milestone outcomes, product risks, and work not yet ready for execution. GitHub Issues are the actionable engineering record; repository backlog files preserve the durable product context that should survive individual Issues and pull requests.

Status vocabulary: `proposed`, `ready`, `in_progress`, `blocked`, `implemented`, `validated`, `deferred`.

Priority order is research correctness and provenance; owner-discovery and identity-resolution viability; analyst trust and workflow value; acquisition coverage, reliability, and cost; then advanced AI, scale, and enterprise concerns.

## Current product position

- Milestone 2.2 — Live Local Google Authentication is complete and validated.
- Milestone 3 — Multi-State Data Acquisition and Curation is complete. Issue #32 validated the delivered bounded Utah BEL sample and closed the three-state acquisition milestone.
- Milestone 3.1 — Evidence Convergence and Dynamic Discovery is complete as a validated foundation. The live cohort's unsuccessful version-one quality result remains negative evidence; Issue #55 supplies an offline-validated version-two contract without making another live call.
- Milestone 4 is complete with a change decision. Its proposal, evidence-bounded analysis, research-loop, and analyst-disposition contracts are validated offline; its governed live run stopped before model analysis when the frozen evidence packet did not reproduce. The negative result is preserved and narrows Milestone 5 rather than becoming a quality claim.
- Milestone 4.7 — Live Opportunity Pipeline is complete. It bridged bounded real three-state evidence through source preflight, governed model analysis, attributable disposition, and one conservative Utah review candidate.
- Issue #92 preserves the deferred Utah/OpenAI ambiguity follow-up; it does not block the accepted Utah case from remaining in human review.
- Milestone 5 — Opportunity Intelligence Workflows is complete as of September 10, 2026. Issues #95–#100 delivered deterministic score provenance, saved research and watchlists, bounded manual refresh, gated in-app alerts, provenance-safe exports, and reconciled closeout. Autonomous enrichment remains gated.
- Milestone 5.1 — Workflow Traceability and Effectiveness is complete as of September 10, 2026. Issues #107, #108, and #110 closed the two post-audit gaps without rewriting Milestone 5 history or activating Milestone 6.
- Milestone 6 — Operational Productization is complete as of September 11, 2026. Issues #114–#119 delivered safe schema upgrades, bounded pilot authorization, proven recovery, aggregate operational visibility, and measured deployment hardening.
- The approved discovery lead prioritization follow-up (working label Milestone 6.1) is implemented in PR #127 under retrospective Issue #126. See `milestones/milestone-6.1.md` for scope, validation and the process repair. Milestone 7 is approved and in progress under GitHub milestone 12 and Issues #128–#130. Typed transition policies and evidence-review integration are implemented in #128/#129; Issue #130 now has a validated offline comparative evaluation and completed approved source preflight (11 searches; three eligible frozen packets; no model analysis or promotion). Three evidence-verified analysis requests are now frozen offline under #130; model execution remains unapproved. Live quality and the milestone closeout decision remain open. Live quality gates remain explicit.
- `docs/project/current-state.md` is the detailed implementation and validation handoff.

## Forward sequence

1. Milestone 3 has completed the bounded Colorado, Utah, and Texas evidence-supply foundation.
2. Milestone 3.1 has completed evidence convergence, bounded public research, and the provider-neutral search/model foundation over traceable evidence.
3. Milestone 4 productizes a dynamic, evidence-backed opportunity-research loop, analyst disposition, and a separately approved end-to-end live quality evaluation.
4. Milestone 4.7 proves the operational bridge from bounded live state evidence to preflighted, reviewed opportunity candidates.
5. Milestone 5 turns reviewed evidence and analysis into ongoing opportunity workflows after its prerequisites are met.
6. Milestone 5.1 completes alert traceability and workflow-effectiveness measurement found missing in the Milestone 5 audit.
7. Milestone 6 hardens a proven pilot for dependable multi-user operation without assuming distributed infrastructure.
8. Milestone 7 broadens transition intelligence beyond the initial mortality-related signal after precision and source sustainability are demonstrated.

This ordering is a product constraint: model-assisted discovery must consume traceable curated evidence, and opportunity workflows must consume validated outputs. Neither may create a parallel path that bypasses provenance, deterministic validation, or human review.

## Source-of-truth contract

- `docs/product/roadmap.md` owns milestone sequence and product-level outcomes.
- `backlog/milestones/` owns durable milestone scope, definition of done, result, and validation status.
- `backlog/items/` owns proposed or deferred work that is not yet implementation-ready.
- GitHub milestones group approved execution work; GitHub Issues define actionable tasks; pull requests provide implementation and validation evidence.
- `docs/project/current-state.md` records what actually works, what is partial, and what remains missing.

When these records disagree, do not silently choose the most optimistic account. Inspect the implementation and validation evidence, correct the repository record in the active pull request, and reconcile GitHub state.

## Milestone lifecycle

When starting an approved milestone:

1. Create or update its `backlog/milestones/` file with goal, scope, definition of done, and `in_progress` status.
2. Create the corresponding GitHub milestone and implementation-ready Issues only for approved work.
3. Update this file and `docs/project/current-state.md` to name the active milestone.

Before closing a milestone:

1. Validate the implementation and record only evidence that was actually observed.
2. Update the milestone file with its result and final status.
3. Reconcile related `backlog/items/`, the product roadmap, and architecture or decision records when scope or knowledge changed.
4. Update this file and `docs/project/current-state.md` with the next approved state; use “no active milestone” when the next milestone has not been authorized.
5. Ensure the closing pull request links its GitHub Issue and includes the documentation changes, then close the GitHub milestone only after the pull request passes validation and merges.

CI can validate repository contents, but it cannot prove that narrative product status and GitHub milestone state are semantically aligned. The engineer or agent closing the milestone owns that reconciliation.

Issue #130: the approved three-call analysis attempt stopped at the provider input-count gate before generation. Zero model analyses or promotions occurred; the failure and five-cent reservation are retained. All 295 backend/API tests pass for the one-shot execution increment. Live quality and human value remain unmeasured; another attempt requires a new recorded decision.

September 14, Issue #130: the explicitly approved three-packet model retry produced one incomplete and two consistency-invalid responses, zero valid observations/promotions, and $0.0117305 estimated generation cost. All 295 backend/API tests passed. Live quality remains unvalidated; next work is offline prompt/validator alignment and safe per-check diagnostics. Further live execution is not authorized.

Issue #130 offline follow-up: a separate observation-v2 contract removes model-authored disposition, derives research guidance deterministically, and preserves useful uncertain observations. Future execution failures retain safe per-check codes. All 308 backend/API tests pass with zero new external calls. This does not explain the discarded live outputs or activate v2 live execution; Milestone 7 remains open.

Issue #130 integration follow-up: observation v2 is wired into preparation v2 and execution v3. The revised hash-pinned bundle preserves the same three public-source packets and proposes 6,000 output tokens per call with a $0.15 total ceiling. All 315 backend/API tests pass; mocked execution validates separate model observations and deterministic dispositions, approval/hash/retry gates, and preserved execution history. No new external calls ran. The revised requests require explicit approval before a live run; Milestone 7 remains open.

Issue #130 approved observation-v2 evaluation: execution v3 returned 3/3 contract-valid observations, preserved useful research clues without ownership assertions, and made zero promotions. Three model calls cost an estimated $0.011985 ($0.15 reserved; invoice unavailable). Earlier failed outcomes remain intact. Agent source review identified temporal ambiguity in active-operation labels and an overly strong geographic exclusion; contract validity is not a live precision pass. Human usefulness/time remain unmeasured. The run approval is exhausted; next work is human review and offline temporal/geographic clarification. Milestone 7 remains open.

Issue #130 offline contextual review now preserves model observations alongside attributed, cited temporal/geographic interpretation. Historical or undated operations do not establish assessment-date activity; addresses and legal domicile alone do not establish requested-state operating presence or exclusion. A hash-bound, credential-free report reviewed the retained three-packet run without mutating it: all three current-operation conclusions are unknown, and Savage Utah/Premier Colorado operating fit become unknown while its original output remains intact. All 342 backend/API tests passed, including 27 new fictional context/report checks. No external calls, database writes or promotions occurred. Human usefulness and representative live quality remain unmeasured; Milestone 7 stays open.

Issue #130 analyst evaluation review adds `/research/evaluation`, linked from Research, for explicitly opening a browser-local package with retained source text, original model observations and separate contextual guidance. It exports self-attributed usefulness feedback bound to the selected file SHA-256; missing judgments and duration stay missing, and time saved/analyst acceptance are not inferred. The offline CLI can generate the package from the exact retained artifacts. All 343 backend/API and 19 frontend tests passed; the production build passed with the existing chunk warning and the fictional page/export was rendered at a narrow viewport. No source/model calls, application database writes or promotions occurred. Actual human feedback and representative quality remain outstanding; Milestone 7 is open.

Issue #130 now validates explicitly selected usefulness exports against the exact retained review package and produces offline metrics with explicit judgment/packet denominators. Duplicate reviewer-slot judgments, mismatched hashes, invalid times and malformed records are refused. Missing review time, time saved and precision remain unavailable; self-reported identity is not authenticated. All 375 backend/API tests passed, including 32 new validation/aggregation checks. A no-input run over the real package correctly reports 0/3 coverage and unavailable usefulness; it is not evidence that no feedback file exists elsewhere. No browser, database or external calls were used. Milestone 7 remains open for actual human feedback and remaining quality decisions.
