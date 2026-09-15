# Case workflow measures

Issue #182 extends M8.5 through optional feedback in the existing append-only `CaseDecision` content. No schema migration or new evidence store is needed. A useful/not-useful judgment requires a reason; optional self-reported duration is a strict integer from 1 to 86400 seconds. Missing feedback and blank time remain unmeasured. Feedback is human interpretation for the stated purpose/version, never deterministic evidence truth. Existing review permission, attribution, atomic audit, stale correction and actor-safe UUID replay apply; legacy omitted feedback stays omitted.

## Read contract and denominators

Authenticated `GET /api/research/case-workflow-measures?page=1` reports `case-workflow-measures-v1`. It selects the latest shared decision per case before aggregation. All retained research cases form the workspace denominator, including stopped/unresolved cases. Superseded decisions stay in history but do not inflate current-case measures. Cases with no decision are reported separately from decided cases with missing usefulness. Purpose groups are based on current decisions only; the report does not invent a purpose for an unreviewed case.

Useful percentage divides useful by useful plus not-useful judgments, not all cases. With no assessments it is null. Median duration uses only present durations on current decisions and exposes the sample size. It is neither cumulative effort nor time saved; elapsed browser time is not inferred. Ten current decisions per page link to cases with reviewer, brief version, purpose, reason and individual duration. This is the existing trusted single-organization read boundary from ADR-012, not a personal productivity ranking. Personal monitoring content remains excluded.

## Cost boundary

Discovery, follow-up and extraction attempt reservations are grouped separately by status and summed once per attempt, including failures and interruptions. Run totals are not added again. Units are USD cents. These are authorization reservations, not provider invoices or measured spend. Legacy research/model runs, document retrieval, source refresh and infrastructure are excluded explicitly. Zero recorded reservations therefore does not establish zero total research cost. Existing source-workflow effectiveness reporting remains available; complete cost coverage and the frozen M8.6 cohort ledger still require validation.

## UI and observed validation

The decision form captures optional feedback and preserves the same payload on lost-response retry. Loading another brief resets feedback. History labels missing feedback/time; the overview retains negative and absent judgments and explains denominators, scope and limits. No automatic human-quality pass is derived from workspace counts, fictional data or provider success.

All 551 backend/API tests, 57 frontend tests and TypeScript/production build passed (existing chunk warning). Regression coverage includes empty databases, corrected decisions, mixed missing/negative feedback, median sample sizes, strict duration bounds, legacy replay, role denial, pagination, retained failed/interrupted reservations and inert source-like text. Desktop/390px forms and overview were inspected; fictional negative feedback and 120 test seconds survived UI save/reload while historical feedback remained unchanged. These are agent QA fixtures, not actual human usefulness judgments. No migration, live calls or operational-corpus writes ran. Full explicit-refresh workflow validation, complete cost coverage and actual M8.6 human evaluation remain open.

## Integrated refresh acceptance (#184)

The in-policy fictional monitoring refresh journey now passes through explicit follow-up, access review, retrieval, extraction, saved brief comparison, reviewer decision and manual reschedule. Positive/empty regressions verify single provider execution per request key, unchanged original budgets, retained unanswered questions and historical snapshots/decisions/monitoring after database reopen. The rendered UI retains no-observation output and leaves usefulness unassessed. All 553 backend/API tests, 57 frontend tests and TypeScript/build pass; desktop/390px and reload inspected. No live calls, migration or operational-corpus writes. Old-case date-policy renewal, complete cost coverage and actual human evaluation remain open. See [acceptance record](../research/milestone8-monitoring-refresh.md).
