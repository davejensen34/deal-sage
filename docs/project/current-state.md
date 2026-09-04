# Current state

## Active milestone

Milestone 1 — Evidence and Analyst Foundation is implemented and undergoing final reconciliation in GitHub Issue #1. It originally entered `main` as commit `d9fa99d` before the Issue/PR operating model existed; no retroactive process was invented.

## What works and has been validated

- React/Vite dashboard and candidate list consume persisted API data.
- SQLite startup auto-creates and seeds 18 fictional candidates and 36 evidence items.
- Search, status/state/confidence filters, pagination, and API sorting work.
- Candidate detail exposes business/person/signal, three confidence values, rationale, conflicts, gaps, evidence provenance, and audit history.
- Validate/reject/watchlist/more-research actions and analyst notes persist and create audit events.
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

Live sources, source registry/adapters, autonomous acquisition, real transition signals, distributed work, enterprise authentication, multi-user authorization, production monitoring, backups, semantic search, and national coverage. These belong to later milestones.

## AI state

Candidate evidence summary is the only bounded AI capability. The UI and endpoint are optional and disabled without configuration. The minimal app works without AI. SDK imports are lazy; SDKs are optional local dependencies and are currently absent from the production Docker image. Live provider behavior, token capture, and output-quality evaluation are untested.

## Highest risks

1. Whether public sources expose actual SMB owners/controllers with sufficient quality and permitted programmatic access.
2. Identity-resolution precision and false-positive harm.
3. Distinguishing legal roles from control across jurisdictions and stale filings.
4. Research acquisition reliability and sustainable source maintenance.
5. Analyst trust if score fixtures and evidence-derived recalculation diverge.

## Next

Complete Issue #1 through CI and PR. Then, only with user direction, open Milestone 2 with one narrow owner-discovery research experiment described in `backlog/milestones/milestone-2.md`.

## Latest validation

Reconciliation exercised 9 backend/API tests, the initial migration from an empty database, 1 frontend component test, the production frontend build, Compose configuration, and the full Nginx/FastAPI/PostgreSQL stack. Rendered inspection covered the dashboard, sortable/searchable candidate list, registered-agent false-positive detail, evidence and uncertainty hierarchy, decision modal, persisted watchlist decision/note, and updated audit history. No material clipping or hierarchy defect was observed at the desktop validation viewport; broader breakpoint coverage remains partial.
