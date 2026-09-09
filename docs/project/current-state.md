# Current state

## Milestone status

Milestone 4.7 — Live Opportunity Pipeline is active as of September 9, 2026. It follows Milestone 4's change decision by assembling bounded real Colorado, Utah, and Texas evidence into one operational corpus, preflighting reproducible transition packets, and separately gating model analysis into a human-reviewed queue. Milestone 5 remains proposed and is not active.

## What works and has been validated

- React/Vite dashboard and candidate list consume persisted API data.
- SQLite startup auto-creates and seeds 18 fictional candidates and 36 evidence items.
- Search, status/state/confidence filters, pagination, and API sorting work.
- Candidate detail exposes business/person/signal, three confidence values, rationale, conflicts, gaps, evidence provenance, and audit history.
- Validate/reject/watchlist/more-research actions and analyst notes persist and create audit events.
- Persisted research trails represent target, discovery, authoritative anchor, business/web validation, person discovery, relationship validation, and owner readiness with actual funnel counts.
- Demo identity remains credential-free; provider-neutral OIDC, Google discovery, subject-keyed JIT users, allowlists, sessions, logout, and user-linked audit attribution are implemented and integration-tested.
- Real Google authentication was validated end to end on localhost: discovery and token exchange succeeded, a verified Google identity created an active JIT user, the signed session loaded the protected workspace, and an authenticated candidate view produced a user-linked audit event.
- The version-two model evaluation contract separates seven case dimensions, rejects internal contradictions deterministically, distinguishes incomplete/refusal/invalid/failed provider outcomes, records split token usage, and produces per-dimension metrics. Seven fictional case shapes pass through both provider mocks without live calls.
- Model proposals persist as immutable, case-linked execution results with evidence or claim lineage, complete provider/version provenance, safe structured output, split usage, latency, bounded cost, and explicit failure outcomes. Non-completed calls retain no provider payload or exception body.
- Structured business extraction and ambiguity analysis operate on selected case evidence and claims through the provider-neutral interface. Deterministic post-validation rejects unsupported citations, name-only resolution, relationship/timeline conflicts, and ownership proposals lacking explicit owner-role evidence; invalid output is not retained.
- Authenticated analysts can accept, correct, reject, or defer immutable model proposals with a rationale and case-local evidence/claim lineage. The Research workspace displays source-linked provider output, safe execution provenance, and the additive human disposition history as visibly separate layers; corrections never rewrite the original proposal.
- The authorized $5 Utah BEL delivery landed as three immutable private CSV artifacts plus a replayable joined package. It produced 188 businesses and 470 relationship assertions, including 205 explicit owner-role candidates, with clean joins, no quarantine, and aggregate-only analyst reporting. Source roles remain unvalidated ownership assertions.
- Milestone 4.7 assembles one ignored operational corpus from a new 25-record Colorado refresh, a new 25-record Texas refresh, and the exact four retained Utah delivery artifacts. It contains 54 immutable artifacts and 736 curated records with zero quarantine; an identical repeat retained the same totals without paid search or model calls.
- A three-state Milestone 4.7 transition cohort is preflighted in the same local corpus. Its six ordinary public pages all passed retrieval, exact-excerpt verification, and SHA-256 artifact verification before model execution; the full frozen packet remains ignored and the repository exposes only aggregate-safe measures.
- Credential-free mode, frontend build/tests, backend/API tests, Compose configuration, and a full Nginx/FastAPI/PostgreSQL stack were exercised during reconciliation.

## Implemented but not fully validated

- OpenAI and Anthropic adapters support bounded summaries and schema-validated extraction behind a provider interface. Both processed the approved public-evidence cohort; the resulting evaluation failures are recorded rather than represented as validation.
- Alembic has an initial schema revision validated against an empty SQLite database.
- Responsive styles exist; desktop rendered workflows are the primary validation target.

## Partial

- The Milestone 3 landing models and service preserve acquisition runs, immutable content-addressed artifacts, versioned curated subjects, field lineage, replay, and quarantine. Colorado, Utah, and Texas bounded live sources were exercised successfully; none provides comprehensive statewide beneficial-ownership truth.
- Acquisition-run summaries are available through the authenticated API; detailed raw evidence review and quarantine resolution UI remain deferred.
- Seed case scores are curated persisted fixtures; deterministic scoring functions are tested but feature observations are not yet persisted/recalculated from evidence.
- Analyst notes are structured JSON in `ReviewCase`, not a first-class table.
- Job execution has an in-process interface but no persistent `ResearchJob` model or scheduler.
- Search is portable SQL filtering; FTS5/pg_trgm optimization and a search interface remain deferred.
- Watchlist status works; a dedicated watchlist page is informational.
- Research and Settings routes accurately describe current limits rather than presenting dead controls.

## Missing or intentionally deferred

Autonomous acquisition, live transition-signal sources, validated beneficial-ownership coverage, distributed work, enterprise RBAC/organizations, production monitoring, backups, semantic search, and national coverage. These belong to later milestones.

## AI state

Candidate evidence summaries and case-linked model proposals are UI-exposed AI capabilities. Proposal output is explicitly labeled, retains safe execution provenance and evidence/claim references, and remains non-authoritative until an analyst records a separate disposition. Provider adapters also support schema-validated extraction for controlled validation work. The app remains functional without AI; local Compose includes the optional SDKs, configuration defaults to disabled, requests are time/output bounded, OpenAI storage is off, and provider error bodies are not persisted. Public-evidence output quality was exercised but did not pass: 12/14 corrected-run responses were parseable and only 3/14 matched the conflated top-level pre-label. The replacement contract passes fictional offline fixtures but has no live quality result.

## Highest risks

1. Whether permitted obituary, probate, and publisher feeds provide sufficiently timely and broad signal-first coverage; official vital-record systems do not.
2. Identity-resolution precision and false-positive harm.
3. Distinguishing legal roles from control across jurisdictions and stale filings.
4. Research acquisition reliability and sustainable source maintenance.
5. Analyst trust if score fixtures and evidence-derived recalculation diverge.

## Next

Review and explicitly approve or revise Issue #87 protocol `m4-7-ai-v1-2026-09-09`: OpenAI `gpt-5-mini`, Anthropic `claude-sonnet-4-5`, the three frozen cases, zero search calls, at most twelve model calls, and a USD $1.00 total ceiling. Do not make paid calls or activate Milestone 5 automatically.

Repository documentation was reconciled in Issue #56 before beginning that version-two contract. `docs/README.md` now distinguishes living specifications from historical ADR, milestone, experiment, and validation records; the implementation and this file remain the final truth check when records disagree.

## Latest validation

The current implementation exercises 151 backend/API tests and five frontend tests. All sixteen migrations upgraded, downgraded, and re-upgraded on an empty SQLite database; the production frontend built with its existing large-chunk warning; Compose configuration validated; and a rebuilt PostgreSQL/FastAPI/Nginx stack became healthy, returned `/api/health`, and rendered the local dashboard. The bounded Utah delivery achieved 100% ingestion success across 188 entities, 188 BUSINFO rows, and 470 PRINCIPAL rows; all joins resolved without duplicate keys, orphan rows, or quarantine, and an identical repeat added no artifacts. The optional-provider API image builds with both SDKs. The version-two replacement and Milestone 4.1–4.4 contracts remain validated against fictional fixtures and adapter mocks. The Issue #71 run added three OpenAI web-search calls at a conservative estimated cost of $0.06, landed three immutable artifacts that failed exact-excerpt qualification, and made zero model-analysis calls.

Milestone 2.2 previously validated the real Google browser flow, JIT identity, signed session, and user-linked audit attribution. Credentials remain in the ignored root `.env`; provider tokens are not persisted. Broader breakpoint coverage remains partial.
