# Pilot operational health

DealSage separates process liveness from dependency readiness:

- `GET /live` is unauthenticated and returns only `{"status":"alive"}`. It proves the API process can answer; it does not claim the database, schema, evidence storage, sources, or providers are healthy.
- `GET /api/operations/readiness` requires the operator or administrator capability. Demo mode retains access for local product validation.
- The Settings workspace renders the protected readiness result for permitted roles and discloses no operational details to viewers or analysts.

The readiness result checks database access, the current and expected Alembic revisions, and an actual create/write/delete probe in the evidence root. Capacity is reported only as aggregate bytes. A stale schema or unwritable evidence root marks the result `degraded`.

The rolling 24-hour section reports counts for acquisition, manual source refresh, research steps, and model proposals; safe failure classes; separately labeled recorded cost views; authorization denials; and audit attribution. Cost views are intentionally non-additive because a research step may also be represented by a model proposal. They reflect persisted DealSage estimates or source refresh amounts, not provider invoices.

Audit-write failures are counted when a database transaction containing a new audit event rolls back. This counter is process-local and resets with the API; it complements host logs rather than claiming durable monitoring. Unattributed audit entries remain visible as an aggregate because demo/system history legitimately lacks a pilot user ID, but unexplained growth warrants review.

Operational output never contains names, emails, record IDs, URLs, raw evidence, request metadata, model payloads, or provider error bodies. Historical failure values that do not match a conservative class-name format are collapsed to `redacted`.

No external telemetry or alerting service is required. Operators should inspect readiness before and after upgrades, backup drills, source/model runs, and configuration changes. Production monitoring and external delivery remain deferred.
