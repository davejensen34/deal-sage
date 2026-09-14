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
- The Milestone 6.1 discovery-lead follow-up is implemented in PR #127 under retrospective Issue #126. Milestone 7 remains active under milestone 12: typed policies/review integration, recent-signal intake (#144), business-focused briefs (#145) and bounded evaluation tooling are implemented. The first three-packet human evaluation failed the usefulness gate (0/3 useful); #130 retains that result and the remaining quality decisions. Historical one-shot approvals are exhausted; the later completion envelope is recorded below.
- September 14 update: #144/#145 are implemented; #130 corrective validation used the new approved $5 envelope through 20 searches, 45 HTTP requests and six analysis attempts. Two recent packets await human usefulness judgment, one additional lead remains in date verification, and no ownership match or promotion is claimed. $3.30 reserved / $0.34614475 estimated spend; $1.70 remains. The prior 0/3 useful result and all earlier failures are preserved. Milestone 7 remains active; see `docs/research/milestone7-completion-validation.md`.
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

Issue #130 actual human review now records a failed value gate: 3/3 packets reviewed, 0/3 useful, all three not useful, no deferrals, and 240 seconds of self-reported review time (including a recorded zero). Time saved and promotion precision remain unavailable. The feedback identifies stale signals and review-heavy presentation rather than business insight. Source publication ages were 830/491/245 days at the frozen assessment date. Remediation is tracked in #144 (recent-signal intake before paid analysis) and #145 (business-focused lead briefs). No new live calls ran and Milestone 7 remains open.

Issue #144 application increment: opt-in persisted signal intake now routes cited recent events, announcements, future plans, stale background and date-verification work before model analysis. Dated discovery, lead-priority factors and case narrative counts preserve uncertainty and existing evidence. All 405 backend/API tests pass, including migration upgrade/downgrade protection and no-call/no-reservation checks. The retained preflight, both request bundles, final live results and human feedback still match their recorded hashes. No live calls, existing-database migration or UI deployment ran. Issue #144 remains open for integration into the next versioned frozen evaluation protocol; #145 business-focused briefs and the #130 failed human value gate remain open. See `docs/architecture/signal-intake.md`.

Issue #144 frozen-protocol completion: preparation v3/execution v4 now reuse the application's freshness routing, capture all selected-case transition assertions/conflicts and verified retained source lineage, and reproduce requests/routes/limits before any slot reservation or provider call. Empty cohorts retain exclusion counts without spending; the CLI verifies current evidence before loading credentials. All 429 backend/API tests pass, including 24 new offline freeze/execution/CLI checks. Historical preflight, request, result and feedback hashes still match. No new real-source cohort, live calls, existing database migration or UI deployment ran. Intake implementation is complete; Milestone 7 remains active for #145 business-focused briefs and #130 renewed usefulness/quality evaluation. Future live execution requires separately approved packets and budget.

Issue #145 business briefs now lead the Research workspace with cited business/location/context and size clues, dated transition status, deterministic relevance guidance, unresolved conflicts and a specific next evidence gap. Recent eligible signals precede undated review and historical/public-company background. Missing financials remain unknown; ambiguous names and third-party estimates retain their uncertainty. Original model insight and analyst review remain separate. Historical experiment failures no longer hide briefs or the evaluation link. Validation: all 432 backend/API tests and all 24 frontend tests, TypeScript and the production build passed with the existing chunk warning. Five fictional API-derived cases were rendered at desktop and 390px viewport, with no horizontal overflow and working source/audit expansion. No live calls, real-data writes, migration or deployment ran. This completes the presentation implementation, not the #130 value gate: the retained result remains 0/3 useful. Next prepare a concrete recent-cohort acquisition/evaluation envelope for separate approval, then measure human usefulness again. See `docs/architecture/business-briefs.md`.

Issue #130 recent discovery is prepared under `m7-recent-discovery-v1`: eight frozen name-free CO/UT/TX queries, one per signal family, with a proposed 90-day assessment ending 2026-09-14. The discovery-only runner shares the application search request/parser, reconstructs approved requests and caps, persists one-shot claims/reservations before calls, and stops on failures without retries or replacement queries. It writes only local discovery artifacts, with no direct retrieval, registry access, analysis or application database mutation. All 457 backend/API tests passed, including 25 new guard/SDK/CLI tests. No UI changed and no live query ran. The exact bundle SHA-256 is `838a49f7f1b79f604b3913f5445bd3b1ed76e3a0505df282728bd6ab7388c62f`; explicit approval of these queries to OpenAI, the 90-day window and a $1 ceiling remains pending. Actual publisher/access review precedes a separately bounded retrieval stage. The retained 0/3 usefulness result is unchanged, and Milestone 7 remains open. See `docs/research/milestone7-recent-discovery.md` for the complete proposal and remaining gates.

Issue #130 approved recent discovery stopped after its first query. The provider returned 9,058 input and 932 output tokens, but a subsequent ValueError failed response validation; the historical record lacks the per-check detail needed to identify the cause. Zero candidates or source evidence were retained and seven slots were unattempted. The reservation is $0.12; the recorded estimate is $0.0141285 using the planned one-search fee, not an invoice or proof of actual tool count. The result SHA-256 is `60a423857868c2f3a34f1ee85e4c1564da3b11251a24e31488452d3bfc0a11b7`. The one-shot claim and original result remain immutable, and this run approval is exhausted. Future attempts now have safe versioned per-check diagnostics and bounded response-status/model-match/tool-count observations; this cannot reconstruct the discarded response. All 25 discovery guard tests passed before execution and again after the diagnostic change. No retry, direct source/registry retrieval, corpus write, separate analysis or promotion ran. Milestone 7 and #130 remain open, and human usefulness remains 0/3. A new attempt requires a separately versioned, reviewed execution decision; never delete the claim to replay.
