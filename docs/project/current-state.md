# Current state

## Active milestone

Milestone 2.1 — Research Trail and Pilot Identity is complete and validated through Pull Requests #11–#13. Do not open Milestone 3 without user direction.

## What works and has been validated

- React/Vite dashboard and candidate list consume persisted API data.
- SQLite startup auto-creates and seeds 18 fictional candidates and 36 evidence items.
- Search, status/state/confidence filters, pagination, and API sorting work.
- Candidate detail exposes business/person/signal, three confidence values, rationale, conflicts, gaps, evidence provenance, and audit history.
- Validate/reject/watchlist/more-research actions and analyst notes persist and create audit events.
- Persisted research trails represent target, discovery, authoritative anchor, business/web validation, person discovery, relationship validation, and owner readiness with actual funnel counts.
- Demo identity remains credential-free; provider-neutral OIDC, Google discovery, subject-keyed JIT users, allowlists, sessions, logout, and user-linked audit attribution are implemented and mock-tested.
- Credential-free mode, frontend build/tests, backend/API tests, Compose configuration, and a full Nginx/FastAPI/PostgreSQL stack were exercised during reconciliation.

## Implemented but not fully validated

- OpenAI and Anthropic summary adapters exist behind a provider interface; neither provider has received a live request.
- Local evidence storage implements save/read/delete but is not exercised through an API workflow.
- Alembic has an initial schema revision validated against an empty SQLite database.
- Responsive styles exist; desktop rendered workflows are the primary validation target.

## Partial

- Seed case scores are curated persisted fixtures; deterministic scoring functions are tested but feature observations are not yet persisted/recalculated from evidence.
- Analyst notes are structured JSON in `ReviewCase`, not a first-class table.
- Job execution has an in-process interface but no persistent `ResearchJob` model or scheduler.
- Search is portable SQL filtering; FTS5/pg_trgm optimization and a search interface remain deferred.
- Watchlist status works; a dedicated watchlist page is informational.
- Research and Settings routes accurately describe current limits rather than presenting dead controls.

## Missing or intentionally deferred

Owner-capable live sources, autonomous acquisition, real transition signals, distributed work, enterprise RBAC/organizations, production monitoring, backups, semantic search, and national coverage. These belong to later milestones.

## AI state

Candidate evidence summary is the only bounded AI capability. The UI and endpoint are optional and disabled without configuration. The minimal app works without AI. SDK imports are lazy; SDKs are optional local dependencies and are currently absent from the production Docker image. Live provider behavior, token capture, and output-quality evaluation are untested.

## Highest risks

1. Whether another permitted public source exposes actual SMB owners/controllers with sufficient quality; Colorado's bulk dataset does not.
2. Identity-resolution precision and false-positive harm.
3. Distinguishing legal roles from control across jurisdictions and stale filings.
4. Research acquisition reliability and sustainable source maintenance.
5. Analyst trust if score fixtures and evidence-derived recalculation diverge.

## Next

Wait for user direction before opening Milestone 3 — Owner → Transition Signal Discovery.

## Latest validation

Milestone 2.1 validation exercised 23 backend/API/auth tests, 2 frontend tests, upgrade/downgrade through all three migrations, the production frontend build, and the full Nginx/FastAPI/PostgreSQL Compose stack with an existing demo volume. Rendered inspection covered the measured funnel, progressive research trail, owner-readiness boundary, demo identity, and branded login/error states. Google OIDC callback, JIT provisioning, allowlists, session/logout behavior, authenticated API protection, and user-linked audit attribution were mock-validated; Google was not live-provider tested because credentials were not supplied. Broader breakpoint coverage remains partial.
