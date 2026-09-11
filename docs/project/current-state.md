# Current state

## Milestone status

Milestones 5 and 5.1 are complete. Milestone 6 is active under Issues #114–#119, beginning with deployment-safe database upgrade handling. Milestone 7 remains proposed and requires explicit approval.

## What works and has been validated

- React/Vite dashboard and candidate list consume persisted API data.
- Migrated demo databases seed 18 fictional candidates and 36 evidence items.
- Search, status/state/confidence filters, pagination, and API sorting work.
- Candidate detail exposes business/person/signal, three confidence values, rationale, conflicts, gaps, evidence provenance, and audit history.
- Candidate detail exposes an immutable, versioned score assessment with factor inputs, supporting evidence IDs, the conjunctive formula, and an honest `evidence_derived` or `legacy_demo_import` classification. New reviewed-case promotions create evidence-derived assessments and project their deterministic result onto the queue row.
- Validate/reject/watchlist/more-research actions and analyst notes persist and create audit events.
- Authenticated analysts can save and replay named candidate-queue criteria and maintain multiple dedicated watchlists. Watchlists reference existing candidates rather than copying evidence; membership additions and removals are audited.
- Authenticated analysts can explicitly initiate a bounded 1–100 record refresh of the approved free Colorado and Texas sources. Each durable refresh records attribution, contract fingerprint, acquisition-run linkage, aggregate results, actual/approved cost, freshness limitations, and a safe failure code; Utah remains delivery-based and no scheduler is active.
- Analysts may opt into in-app alerts for refresh failure and quarantine on each approved source. Successful refreshes remain quiet, delivery never leaves DealSage, subscriptions never initiate acquisition, and disabling a subscription preserves its prior alert history.
- Alert reads now resolve their durable refresh relationship into source, acquisition run, freshness, safe failure, and aggregate-only quarantine record references. A direct refresh-detail endpoint keeps an alert self-resolving even after its run leaves the bounded history list; no quarantined record content is exposed.
- The Research workspace reports deterministic source-to-review effectiveness: acquisition and refresh volumes, unique artifacts, curated/quarantined outcomes, recorded refresh cost, freshness, durably attributed candidates, analyst decisions, and reason codes. Candidate attribution requires an actual research-case → raw-artifact → acquisition-run chain; unlinked candidates are counted as unattributed and never guessed.
- Authenticated analysts can export the filtered candidate queue as versioned JSON or CSV, bounded to 100 records. The contract retains public evidence references, source-reported relationship semantics, deterministic score method/provenance, freshness, and analyst disposition; it excludes retained source content, analyst notes, model payloads, request metadata, and URL query parameters. Each candidate export is audited.
- Persisted research trails represent target, discovery, authoritative anchor, business/web validation, person discovery, relationship validation, and owner readiness with actual funnel counts.
- Demo identity remains credential-free; provider-neutral OIDC, Google discovery, subject-keyed JIT users, allowlists, sessions, logout, and user-linked audit attribution are implemented and integration-tested.
- Pilot authorization distinguishes viewer, analyst, operator, and administrator permissions on the server. New OIDC users start read-only; existing pilot users retain prior access during migration; local role/activation changes and permission denials are audited without request bodies. OIDC mutations require a same-origin custom header supplied by the web client, while demo remains an explicit non-production role.
- Real Google authentication was validated end to end on localhost: discovery and token exchange succeeded, a verified Google identity created an active JIT user, the signed session loaded the protected workspace, and an authenticated candidate view produced a user-linked audit event.
- The version-two model evaluation contract separates seven case dimensions, rejects internal contradictions deterministically, distinguishes incomplete/refusal/invalid/failed provider outcomes, records split token usage, and produces per-dimension metrics. Seven fictional case shapes pass through both provider mocks without live calls.
- Model proposals persist as immutable, case-linked execution results with evidence or claim lineage, complete provider/version provenance, safe structured output, split usage, latency, bounded cost, and explicit failure outcomes. Non-completed calls retain no provider payload or exception body.
- Structured business extraction and ambiguity analysis operate on selected case evidence and claims through the provider-neutral interface. Deterministic post-validation rejects unsupported citations, name-only resolution, relationship/timeline conflicts, and ownership proposals lacking explicit owner-role evidence; invalid output is not retained.
- Authenticated analysts can accept, correct, reject, or defer immutable model proposals with a rationale and case-local evidence/claim lineage. The Research workspace displays source-linked provider output, safe execution provenance, and the additive human disposition history as visibly separate layers; corrections never rewrite the original proposal.
- The authorized $5 Utah BEL delivery landed as three immutable private CSV artifacts plus a replayable joined package. It produced 188 businesses and 470 relationship assertions, including 205 explicit owner-role candidates, with clean joins, no quarantine, and aggregate-only analyst reporting. Source roles remain unvalidated ownership assertions.
- Milestone 4.7 assembles one ignored operational corpus from a new 25-record Colorado refresh, a new 25-record Texas refresh, and the exact four retained Utah delivery artifacts. It contains 54 immutable artifacts and 736 curated records with zero quarantine; an identical repeat retained the same totals without paid search or model calls.
- A three-state Milestone 4.7 transition cohort is preflighted in the same local corpus. Its six ordinary public pages all passed retrieval, exact-excerpt verification, and SHA-256 artifact verification before model execution; the full frozen packet remains ignored and the repository exposes only aggregate-safe measures.
- The approved Milestone 4.7 AI work made zero search calls and recorded $0.23 aggregate estimated provider cost. Six business extractions completed. The final subject-bound ambiguity contract retained two Utah proposals and one Texas non-owner proposal while deterministically rejecting both Colorado outputs and the Texas Claude output for unsupported ownership interpretation. Dave Jensen deferred Utah/OpenAI, accepted Utah/Claude, and corrected Texas/OpenAI's business status while retaining its non-owner conclusion. Only Utah entered the real `needs_review` queue; Issue #92 tracks the open-ended OpenAI result.
- Credential-free mode, frontend build/tests, backend/API tests, Compose configuration, and a full Nginx/FastAPI/PostgreSQL stack were exercised during reconciliation.
- Compose now gates API startup on a one-shot Alembic migration. Empty and versioned databases upgrade normally; the exact additive gaps left by historical `create_all` startup are repaired and verified before stamping, while unknown partial schemas fail closed. Application startup no longer creates or patches schema.

## Implemented but not fully validated

- OpenAI and Anthropic adapters support bounded summaries and schema-validated extraction behind a provider interface. Both processed the approved public-evidence cohort; the resulting evaluation failures are recorded rather than represented as validation.
- Alembic's full twenty-revision chain is validated against empty databases, and Compose now applies it before API startup.
- Responsive styles exist; desktop rendered workflows are the primary validation target.

## Partial

- The Milestone 3 landing models and service preserve acquisition runs, immutable content-addressed artifacts, versioned curated subjects, field lineage, replay, and quarantine. Colorado, Utah, and Texas bounded live sources were exercised successfully; none provides comprehensive statewide beneficial-ownership truth.
- Acquisition-run summaries are available through the authenticated API; detailed raw evidence review and quarantine resolution UI remain deferred.
- Seed case scores remain curated edge-case fixtures, but their retained component inputs and calculation are now persisted and labeled `legacy_demo_import`; they are not represented as evidence-derived calibration data.
- Analyst notes are structured JSON in `ReviewCase`, not a first-class table.
- Generic job execution still has only an in-process interface and no scheduler. Source refresh is the intentionally narrow exception, with its own persistent `SourceRefresh` execution record.
- Search is portable SQL filtering; FTS5/pg_trgm optimization and a search interface remain deferred.
- Candidate `watchlist` status remains a separate review disposition from analyst-owned named watchlist membership.
- Research and Settings routes accurately describe current limits rather than presenting dead controls.

## Missing or intentionally deferred

Autonomous acquisition, live transition-signal sources, validated beneficial-ownership coverage, distributed work, enterprise RBAC/organizations, production monitoring, backups, semantic search, and national coverage. These belong to later milestones.

## AI state

Candidate evidence summaries and case-linked model proposals are UI-exposed AI capabilities. Proposal output is explicitly labeled, retains safe execution provenance and evidence/claim references, and remains non-authoritative until an analyst records a separate disposition. Provider adapters also support schema-validated extraction for controlled validation work. The app remains functional without AI; local Compose includes the optional SDKs, configuration defaults to disabled, requests are time/output bounded, OpenAI storage is off, and provider error bodies are not persisted. Live Milestone 4.7 execution proved both value and limits: useful structured extraction, provider disagreement, output-cap sensitivity, and the need for deterministic same-subject ownership validation. Three final ambiguity outputs passed and three were rejected. Analyst dispositions are recorded separately, and the evidence-backed Utah case is now in human review rather than validated.

## Highest risks

1. Whether permitted obituary, probate, and publisher feeds provide sufficiently timely and broad signal-first coverage; official vital-record systems do not.
2. Identity-resolution precision and false-positive harm.
3. Distinguishing legal roles from control across jurisdictions and stale filings.
4. Research acquisition reliability and sustainable source maintenance.
5. Analyst trust if score fixtures and evidence-derived recalculation diverge.

## Next

Proceed through Milestone 6 safe upgrades, pilot authorization, recoverability, operational visibility, and measured hardening. Issue #92 remains a deferred OpenAI quality follow-up and does not authorize another paid run.

Repository documentation was reconciled in Issue #56 before beginning that version-two contract. `docs/README.md` now distinguishes living specifications from historical ADR, milestone, experiment, and validation records; the implementation and this file remain the final truth check when records disagree.

## Latest validation

The current implementation exercises 189 backend/API tests and nine frontend tests. All twenty-one migrations upgrade an empty SQLite database, and tests cover verified adoption and refusal of unknown partial unversioned schemas; the newest role revision also downgraded and re-upgraded successfully. The production frontend builds with its existing large-chunk warning, and Compose configuration validates. The migration-gated PostgreSQL/FastAPI/Nginx stack adopted the backed-up historical local volume, reached Alembic head, added the missing lineage/access/token columns, started the API only after migration success, returned health, and changed workflow-effectiveness lineage availability from false to true. The bounded Utah delivery achieved 100% ingestion success across 188 entities, 188 BUSINFO rows, and 470 PRINCIPAL rows; all joins resolved without duplicate keys, orphan rows, or quarantine, and an identical repeat added no artifacts. The optional-provider API image builds with both SDKs. The version-two replacement and Milestone 4.1–4.4 contracts remain validated against fictional fixtures and adapter mocks. The Issue #71 run added three OpenAI web-search calls at a conservative estimated cost of $0.06, landed three immutable artifacts that failed exact-excerpt qualification, and made zero model-analysis calls.

Milestone 6 Issue #114 adds three schema-upgrade tests. All 185 backend tests and eight frontend tests passed, the production frontend built, and Compose config passed. Before touching the existing local PostgreSQL volume, a temporary custom-format backup was written to `/private/tmp/dealsage-before-m6.dump`. The first adoption attempt failed closed on unrecognized missing token columns; after those known migration seams were explicitly added to the recognized contract, adoption completed transactionally at revision `c8f6a0b4e3d1`. Read-only verification confirmed the version and every previously missing column, a demo-mode smoke test returned API health and durable lineage availability, and normal configured authentication was restored. No live source, search, or model calls occurred; external spend was $0.

Milestone 6 Issue #115 adds four backend authorization/access tests and one frontend request-header test. All 189 backend tests and nine frontend tests passed, and the production frontend built with its existing large-chunk warning. Migration 21 upgraded, downgraded to the prior head, and re-upgraded on a fresh SQLite database; the existing PostgreSQL pilot volume reached the same head with its one prior user preserved as active administrator. Tests cover viewer-default JIT identity, analyst review, operator-only cost permissions, payload-free denial audit, explicit role/deactivation changes, and OIDC mutation-header enforcement. Rendered inspection confirmed the existing Google login and demo workspace remained intact; normal configured OIDC mode was restored. No live identity-provider, source, search, or model calls occurred; external spend was $0.

Milestone 5 Issue #95 adds two backend tests for persisted score provenance and evidence-derived recalculation. All 168 backend tests passed, and migration 17 upgraded, downgraded to the prior head, and re-upgraded on a fresh SQLite database. This work made no live search or model calls and incurred $0 external spend.

Milestone 5 Issue #96 adds two backend workflow tests. All 170 backend tests and five frontend tests passed, the production frontend built with its existing large-chunk warning, and all eighteen migrations upgraded with migration 18 successfully downgraded and re-upgraded on a fresh SQLite database. The rebuilt local Compose stack became healthy, and rendered inspection confirmed both the dedicated Watchlists workspace and replayed Colorado/60% candidate filters. This work made no live search or model calls and incurred $0 external spend.

Milestone 5 Issue #97 adds three backend tests and one frontend presentation test. All 173 backend tests and six frontend tests passed, and the production frontend built with its existing large-chunk warning. Two explicitly approved five-record live refreshes then succeeded at $0: Colorado retrieved five records and curated ten subjects including five registered-agent assertions; Texas retrieved and curated five entity records. Both had zero quarantine and zero ownership-supported assertions. Both honestly reported that freshness is not measurable from individual records. No search or model calls occurred.

Milestone 5 Issue #98 adds three backend alert tests and one frontend presentation test. All 176 backend tests and seven frontend tests passed, and the production frontend built with its existing large-chunk warning. Tests cover opt-in scoping, safe failure detail, quarantine triggers, idempotency, read state, disabling without history loss, rejected success noise, and rejected Utah subscriptions. No live source, search, model, email, SMS, or webhook calls occurred; external spend was $0.

Milestone 5 Issue #99 adds three backend export tests. All 179 backend tests and seven frontend tests passed, and the production frontend built with its existing large-chunk warning. A rebuilt PostgreSQL/FastAPI/Nginx stack rendered the candidate queue with JSON and CSV export controls, and a bounded local Texas request returned the versioned contract with one matching record and every content-boundary flag false. No live source, search, or model calls occurred; external spend was $0.

Milestone 5.1 Issue #107 extends the existing alert tests without increasing the suite count. All 179 backend tests and seven frontend tests passed, the production frontend built with its existing large-chunk warning, and rendered inspection confirmed the refresh and alert workspace layout. Tests verify refresh/acquisition/freshness/failure lineage, aggregate-safe quarantine references, direct refresh lookup, and navigation from an alert to its refresh context. No live source, search, or model calls occurred; external spend was $0.

Milestone 5.1 Issue #108 adds three backend tests and one frontend test. All 182 backend tests and eight frontend tests passed, and the production frontend built with its existing large-chunk warning. The deterministic reporting contract was validated against wholly unattributed demo candidates, an explicit research-case/artifact/acquisition lineage fixture, and a legacy-schema capability fallback. A rebuilt local PostgreSQL/FastAPI/Nginx stack returned the aggregate endpoint and rendered the effectiveness panel while explicitly reporting that its long-lived database has not received the evidence-lineage migration. The contract reports cost scope, non-additive multi-source counts, migration availability, and absence of raw content as machine-readable boundaries. No live source, search, or model calls occurred; external spend was $0.

Milestone 4.7 closeout re-ran all 166 backend tests and five frontend tests, the production frontend build, Compose configuration, and all sixteen migrations through upgrade, downgrade, and re-upgrade on a fresh SQLite database. All passed; the existing frontend large-chunk warning remains. No closeout UI behavior changed, so the previously rendered application baseline remains applicable.

Milestone 2.2 previously validated the real Google browser flow, JIT identity, signed session, and user-linked audit attribution. Credentials remain in the ignored root `.env`; provider tokens are not persisted. Broader breakpoint coverage remains partial.
