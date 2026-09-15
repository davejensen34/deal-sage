# Bounded reviewer follow-up search

Issue #172 connects a reviewer-authored question, rationale and exact query to the existing case. The question is retained as `find_independent_evidence` frontier work. It does not require a business name, replace a model proposal, automatically accept a source, or mark the question resolved when a search returns links.

## Authorization and storage

Authenticated reviewers preview and save a plan; existing `execute_ai` permission controls execution/recovery. Creation freezes query/date policy, provider request/pricing, question/rationale and limits, with an actor, stable actor key, UUID and plan hash. Stale creation conflicts; duplicate creation replays only the matching actor/input/hash/case. Plan, frontier question and creation audit commit together.

The original `DiscoveryRun` has a one-per-case contract. Additive `followup_runs`/`followup_attempts` tables retain separate authorization while reusing its execution, result staging and recovery machinery. Each run links one new frontier item; each reserved attempt links an existing `ResearchStep`. Original discovery settings and case budgets are not enlarged. SearchService accepts an internal active-run authorization callback for this separately reserved query; ordinary callers retain their original case-query gate. Follow-up queries still contribute to retained case query history.

Each plan allows one query and one explicit failed retry, ten minutes from first execution, at most ten additional links within an absolute 100-link case ceiling, and 24 USD cents reserved. Provider result limits remain upper bounds. Each case permits at most ten retained follow-up plans, twenty attempts and 240 USD cents reserved. These are conservative reservations, not invoices. A successful or unknown query is not replayed. Further research needs another explicit plan within the case caps.

Case-row admission serializes follow-up executions across plans; only an open case with pending, unexhausted work can start. Reservation, attempt, step and frontier attempt increment commit before I/O. Existing run compare-and-swap controls reject duplicate execution and late results after interrupted recovery. Unknown outcomes retain reservations and history. A successful search leaves the question pending; exhausted attempts leave it blocked, never resolved. Search completion says nothing about ownership or sale intent.

Current case date policy is retained and must still match the submitted query. Existing seven-day plan-age and reviewed search-provider pricing gates apply. This does not add policy renewal for an old case, automatic model-generated planning, execution of an existing model-proposed frontier item, or unattended monitoring. New dated-research policy handling remains a separate design concern for monitoring. The live provider envelope remains the existing reviewed envelope through September 21, 2026; no live availability or new pricing check was performed here.

## UI and validation

Case pages expose question/rationale/query preparation and all ten possible saved follow-ups. `/followups/runs/{id}` reuses durable progress, limits, failed retry and interrupted recovery controls, with an explicit unresolved-question reminder and a link back to the same case. Source review, retrieval, cited extraction and brief saving remain distinct explicit actions.

All 530 backend/API tests and 44 frontend tests passed, together with TypeScript and the production build (existing chunk warning). Coverage includes frozen creation/idempotency, viewer/analyst/operator permissions, separate original budgets, failed retry/empty results, plan caps, stopped cases, provider drift, overlapping execution from a second session, late-response fencing and migration/reopen/downgrade protection.

The isolated fictional case previously created through discovery was extended in the rendered UI through question → preview → saved follow-up → search → source access review → retrieval → extraction → saved brief. The extraction correctly returned no supported observations; the saved brief retained two source references, both model outcomes and the unanswered question. Desktop and 390px form layouts were inspected and corrected. This completes the basic fictional 8.1-to-8.3 engineering journey, not the actual human usefulness gate or live-source evaluation. Only the isolated demo received migration `a172a0b1d836`; no operational-corpus changes or live calls ran.

## Integrated refresh acceptance (#184)

The in-policy fictional monitoring refresh journey now passes through explicit follow-up, access review, retrieval, extraction, saved brief comparison, reviewer decision and manual reschedule. Positive/empty regressions verify single provider execution per request key, unchanged original budgets, retained unanswered questions and historical snapshots/decisions/monitoring after database reopen. The rendered UI retains no-observation output and leaves usefulness unassessed. All 553 backend/API tests, 57 frontend tests and TypeScript/build pass; desktop/390px and reload inspected. No live calls, migration or operational-corpus writes. Old-case date-policy renewal, complete cost coverage and actual human evaluation remain open. See [acceptance record](../research/milestone8-monitoring-refresh.md).
