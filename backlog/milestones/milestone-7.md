# Milestone 7 — Broader Transition Intelligence

Status: in_progress. Approved September 11, 2026; GitHub milestone [12](https://github.com/davejensen34/deal-sage/milestone/12).

Approval starts implementation. It does not establish that historical live precision or source-sustainability gates passed. New live execution remains a separately approved bounded evaluation.

## Goal

Extend DealSage from its first mortality-related signal into a general ownership-transition intelligence platform.

## Intended scope

- Retirement and succession indicators.
- Ownership transfers and founder exits.
- Dissolution, restructuring, and material leadership-change signals.
- Signal-specific evidence, time, identity, and analyst-review policies.
- Comparative precision, coverage, timeliness, cost, and analyst-value measurement.

## Boundary

New signal types must enter the existing evidence and case-resolution path. They may not create opaque scores, bypass source review, or equate leadership change with ownership transition.

## Execution sequence

1. [#128](https://github.com/davejensen34/deal-sage/issues/128): versioned transition policy catalog, authenticated read-only API, offline tests, and milestone activation records.
2. [#129](https://github.com/davejensen34/deal-sage/issues/129): integrate typed evidence, temporal uncertainty and identity requirements into the existing review path and analyst UI; remove death-only and Utah-only promotion assumptions.
3. [#130](https://github.com/davejensen34/deal-sage/issues/130): comparative offline cohort and measures, bounded live-evaluation protocol, and outcome reconciliation.

4. [#144](https://github.com/davejensen34/deal-sage/issues/144): recent-signal intake before paid analysis, following the failed human-value evaluation.
5. [#145](https://github.com/davejensen34/deal-sage/issues/145): business-focused lead briefs and another explicit usefulness evaluation.

## Definition of done

- All eight signal families have explicit subject, evidence, temporal and ownership policies.
- The existing research path preserves typed signals and uncertainty through attributable human review, without automatic ownership or successor claims.
- Rendered UI exposes the relevant evidence, limitations and next questions.
- Regression fixtures cover supported, ambiguous, contradictory and cross-subject cases, including existing mortality behavior.
- Comparative measures report denominators, abstention, timeliness, cost and analyst outcomes without presenting fictional results as live precision.
- Closing PR reconciles implementation, observed validation and remaining live quality gates across milestone, backlog, roadmap and current state. Unmet gates require an explicit recorded outcome or product change decision, not an implied pass.

## First increment and remaining gaps

Issue #128 provides `transition-policy-v1` research guidance at `GET /api/research/transition-policies`. Issue #129 integrates the catalog into typed claims, case narratives and promotion guards; no new source integrations are added. Existing stored signal values remain unchanged; unknown values do not silently resolve to a death policy. `ownership_change` is the canonical transfer type from ADR-004. Estate transition and other future types need their own reviewed policies.

Issue #129 replaces mortality-only and Utah-specific promotion assumptions with typed evidence and unknown current activity. Latest analyst acceptance, same-case lineage and non-name identity anchors are required; unresolved entity/owner cases and contradictions remain in research. Live sources, calibrated recommendation quality, comprehensive ownership coverage, and automated acquisition are not delivered by the catalog. Issue #92 remains deferred; prior research history and negative results are preserved.

## Observed validation

Issue #128: Windows backend/API suite passed with 222 tests, run from `apps/api`. The catalog's immutable guidance, unknown-type rejection, read-only route and OIDC authentication boundary were exercised offline. No UI changed and no external research/model calls were made. CI and merge evidence belong to the linked PR; this does not close Milestone 7.

Issue #129: 265 backend/API tests and 14 frontend tests passed on Windows. The production build passed with its existing large-chunk warning. A separate fictional SQLite database was migrated and served with providers disabled for rendered browser inspection of leadership-change evidence, event/publication timing, ownership limitations, and model/analyst separation. Migration tests preserved historical activity values and refused a downgrade that would erase unknowns. No existing research database was used for fixture validation; external research/model spend was $0. Issue #130 now has an offline evaluation with 64 fictional cases: 16 promotions, 48 abstentions and no execution failures. All 272 backend/API tests pass. Live validation and milestone closeout remain open; see `docs/research/milestone7-evaluation.md` for measures, limitations and the completed eight-slot source preflight.

The approved source preflight made 11 searches and 11 HTTP requests at $0.153653 estimated search cost. Four pages landed; one was excluded after identifying an unresolved publisher contract, leaving three frozen packets including two fit-mismatch controls. No analysis model, registry request, Utah lookup or promotion ran. All 277 backend/API tests pass. Access-review replay and safe content extraction remain gaps; the next analysis envelope is proposed, not authorized.

Issue #130 analysis preparation now verifies the retained cohort and read-only database lineage, freezes three source-only provider requests with separate expectations, and tests independent target-fit observations. All 286 backend/API tests pass. Preparation made zero external calls and did not reopen cases. The frozen bundle remains unapproved; see the evaluation record for its fingerprint and execution prerequisites.

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
