# Current state

## Active milestone

Milestone 2 — Business and Owner Discovery Proof is complete and validated in Pull Request #7. The Colorado experiment produced a deliberate negative result: the official bulk source is suitable for entity and registered-agent evidence, but not owner discovery. Do not open Milestone 3 without user direction.

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

Owner-capable live sources, autonomous acquisition, real transition signals, distributed work, enterprise authentication, multi-user authorization, production monitoring, backups, semantic search, and national coverage. These belong to later milestones.

## AI state

Candidate evidence summary is the only bounded AI capability. The UI and endpoint are optional and disabled without configuration. The minimal app works without AI. SDK imports are lazy; SDKs are optional local dependencies and are currently absent from the production Docker image. Live provider behavior, token capture, and output-quality evaluation are untested.

## Highest risks

1. Whether another permitted public source exposes actual SMB owners/controllers with sufficient quality; Colorado's bulk dataset does not.
2. Identity-resolution precision and false-positive harm.
3. Distinguishing legal roles from control across jurisdictions and stale filings.
4. Research acquisition reliability and sustainable source maintenance.
5. Analyst trust if score fixtures and evidence-derived recalculation diverge.

## Next

Wait for user direction before opening Milestone 3. The next source experiment should reject schemas without explicit owner/controller roles before adapter implementation.

## Latest validation

Milestone 2 validation exercised 14 backend/API tests, 1 frontend component test, the production frontend build, and the full Nginx/FastAPI/PostgreSQL Compose stack. A live bounded Colorado request retrieved 50 records successfully in 496 ms at zero marginal API cost. Rendered inspection covered the Research decision, metrics, role taxonomy, source contract, and limitations; reverse-proxy API requests were verified after correcting base-path normalization. Broader breakpoint coverage remains partial.
