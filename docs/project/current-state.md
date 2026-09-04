# Current state

## Active milestone

Milestone 3.1 — Evidence Convergence and Dynamic Discovery is active. Issues #33 through #45 established the common case spine, bounded discovery/planning, precise clues, bidirectional resolution, and explainable confidence. Issue #46 adds the analyst narrative and truthful validation assessment. Milestone 3 remains open but safely paused at Issue #32 while the authorized Utah BEL delivery is pending; its tested importer preparation is preserved on `feature/32-utah-live-sample`.

## What works and has been validated

- React/Vite dashboard and candidate list consume persisted API data.
- SQLite startup auto-creates and seeds 18 fictional candidates and 36 evidence items.
- Search, status/state/confidence filters, pagination, and API sorting work.
- Candidate detail exposes business/person/signal, three confidence values, rationale, conflicts, gaps, evidence provenance, and audit history.
- Validate/reject/watchlist/more-research actions and analyst notes persist and create audit events.
- Persisted research trails represent target, discovery, authoritative anchor, business/web validation, person discovery, relationship validation, and owner readiness with actual funnel counts.
- Demo identity remains credential-free; provider-neutral OIDC, Google discovery, subject-keyed JIT users, allowlists, sessions, logout, and user-linked audit attribution are implemented and integration-tested.
- Real Google authentication was validated end to end on localhost: discovery and token exchange succeeded, a verified Google identity created an active JIT user, the signed session loaded the protected workspace, and an authenticated candidate view produced a user-linked audit event.
- Credential-free mode, frontend build/tests, backend/API tests, Compose configuration, and a full Nginx/FastAPI/PostgreSQL stack were exercised during reconciliation.

## Implemented but not fully validated

- OpenAI and Anthropic summary adapters exist behind a provider interface; neither provider has received a live request.
- Alembic has an initial schema revision validated against an empty SQLite database.
- Responsive styles exist; desktop rendered workflows are the primary validation target.

## Partial

- The Milestone 3 landing models and service preserve acquisition runs, immutable content-addressed artifacts, versioned curated subjects, field lineage, replay, and quarantine. Colorado and Texas bounded live sources were exercised successfully; Utah's authorized live BEL delivery remains pending in Issue #32.
- Acquisition-run summaries are available through the authenticated API; detailed raw evidence review and quarantine resolution UI remain deferred.
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

1. Whether permitted obituary, probate, and publisher feeds provide sufficiently timely and broad signal-first coverage; official vital-record systems do not.
2. Identity-resolution precision and false-positive harm.
3. Distinguishing legal roles from control across jurisdictions and stale filings.
4. Research acquisition reliability and sustainable source maintenance.
5. Analyst trust if score fixtures and evidence-derived recalculation diverge.

## Next

Merge Issue #46's analyst narrative and validation assessment, then resolve its explicitly recorded live search/model and real-case validation gaps before closing Milestone 3.1. Resume Issue #32 immediately when the Utah BEL archive arrives; its currently forecast documentation conflicts are recorded on that issue.

## Latest validation

The current Milestone 3.1 implementation exercises 88 backend/API tests and upgrade/downgrade/upgrade through all eleven migrations on an empty SQLite database, plus four frontend tests, a production build, and rendered desktop review. The narrative zero-state is truthful because no convergence cases are persisted locally. Live search/model and real-case validation remain unclaimed. Earlier Milestone 3 validation exercised bounded Colorado and Texas sources; live Utah validation remains pending delivery, with the branch conflict forecast currently limited to two documentation files.

Milestone 2.2 previously validated the real Google browser flow, JIT identity, signed session, and user-linked audit attribution. Credentials remain in the ignored root `.env`; provider tokens are not persisted. Broader breakpoint coverage remains partial.
