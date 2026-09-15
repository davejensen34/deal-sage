# Personal case monitoring

Issue #178 is the first M8.5 increment. It extends the existing Watchlists workspace with manual research-case follow-up dates. Candidate watchlists still reference candidates; this queue references `ResearchCase` directly so unresolved and stopped cases need no promotion. Existing source-refresh alerts report ingestion failures/quarantines and are not a suitable case-review scheduler. No new background scheduler, recurring infrastructure or external notification is introduced.

## Retained updates and ownership

`CaseMonitoring` holds case ID, stable owner key, display actor, UTC-calendar review date, active/paused state, question, reason, request UUID and prior record ID. Each update appends a record, including pauses and reschedules. The case-row lock serializes first writes and updates; the expected prior record must match the latest record for this owner/case. An identical owner/case/payload/UUID retry returns the committed record, even after a later update. A conflicting key or stale prior record fails without changing history. Audit and record commit together. This never changes the shared reviewer decision, candidate state, evidence or research budget/status.

The owner key is a hash of authenticated provider and subject. Every queue/history read filters this identity, and writes require the existing `personalize` permission from ADR-012. Administrative role does not grant access to another person's queue. This follows the existing personal-workflow boundary within the single-organization pilot; it is not enterprise tenant isolation. No delete endpoint exists; pause preserves history.

## Due work

`GET /api/monitoring/cases?scope=due&page=1` returns ten current entries, a next-page indicator, the total due count across the user's queue, and the UTC assessment date. Supported scopes are due, active, paused and all. The query first selects the newest ID per owner/case and only then applies date/state filters, preventing an old overdue row from resurfacing after a pause or reschedule. Active entries are due when their stored date is on or before the current UTC date. Paused entries retain their dates but are never due. The UI states this UTC-calendar convention explicitly.

`GET /api/monitoring/cases/{case_id}?page=1` returns the user's latest record and ten history rows. `POST` appends a schedule update. A valid ISO calendar date, meaningful question and reason are required. Dates may be in the past to retain already-due work. Recording a new date does not claim a review was completed, record time saved, or authorize research. Historical entries are labeled previous schedules rather than active reminders.

Case pages provide explicit load/edit/save and history. Lost-response retries reuse the UUID and payload; a conflict can be recovered by reloading current monitoring. The Watchlists queue links directly to each case and offers scope and pagination controls. Viewers are read-only. Migration `c178a0b1d838` follows `b174a0b1d837` and refuses downgrade when monitoring history exists.

## Observed validation and remaining work

All 544 backend/API tests, 52 frontend tests, TypeScript and production build passed (existing chunk warning). Tests cover unresolved/stopped-case preservation, personal ownership, permission denial, date boundaries, paused/rescheduled filtering, pagination, stale writes/retries and migration/reopen/downgrade protection. Desktop and 390px fictional save, queue navigation, reschedule/pause and retained-history checks passed; the old due item disappeared and the paused record survived navigation/reload. Only the isolated fictional database received the migration. No live calls or operational-corpus writes ran.

M8.5 remains open for explicit refresh/source-version comparisons and practical review/usefulness/time/cost measures. This increment does not establish that new evidence exists, complete a monitoring question, or schedule provider calls. M8.6 still requires actual human usefulness judgments and the separately frozen live cohort.
