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

## Definition of done

- All eight signal families have explicit subject, evidence, temporal and ownership policies.
- The existing research path preserves typed signals and uncertainty through attributable human review, without automatic ownership or successor claims.
- Rendered UI exposes the relevant evidence, limitations and next questions.
- Regression fixtures cover supported, ambiguous, contradictory and cross-subject cases, including existing mortality behavior.
- Comparative measures report denominators, abstention, timeliness, cost and analyst outcomes without presenting fictional results as live precision.
- Closing PR reconciles implementation, observed validation and remaining live quality gates across milestone, backlog, roadmap and current state. Unmet gates require an explicit recorded outcome or product change decision, not an implied pass.

## First increment and remaining gaps

Issue #128 provides `transition-policy-v1` research guidance at `GET /api/research/transition-policies`. The catalog does not yet enforce promotion policy or add source integrations. Existing stored signal values remain unchanged; unknown values do not silently resolve to a death policy. `ownership_change` is the canonical transfer type from ADR-004. Estate transition and other future types need their own reviewed policies.

The existing queue bridge still assumes mortality, former ownership and Utah-specific follow-up. Issue #129 owns its replacement. Live sources, calibrated recommendation quality, comprehensive ownership coverage, and automated acquisition are not delivered by the catalog. Issue #92 remains deferred; prior research history and negative results are preserved.

## Observed validation

Issue #128: Windows backend/API suite passed with 222 tests, run from `apps/api`. The catalog's immutable guidance, unknown-type rejection, read-only route and OIDC authentication boundary were exercised offline. No UI changed and no external research/model calls were made. CI and merge evidence belong to the linked PR; this does not close Milestone 7.
