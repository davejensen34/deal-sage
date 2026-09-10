# Current state

## Milestone status

Milestone 4.7 — Live Opportunity Pipeline is complete as of September 9, 2026. Milestone 5 — Opportunity Intelligence Workflows was explicitly approved and activated on September 10, 2026. GitHub Issues #95–#100 track its work, beginning with persisted candidate score provenance in #95.

## What works and has been validated

- React/Vite dashboard and candidate list consume persisted API data.
- SQLite startup auto-creates and seeds 18 fictional candidates and 36 evidence items.
- Search, status/state/confidence filters, pagination, and API sorting work.
- Candidate detail exposes business/person/signal, three confidence values, rationale, conflicts, gaps, evidence provenance, and audit history.
- Candidate detail exposes an immutable, versioned score assessment with factor inputs, supporting evidence IDs, the conjunctive formula, and an honest `evidence_derived` or `legacy_demo_import` classification. New reviewed-case promotions create evidence-derived assessments and project their deterministic result onto the queue row.
- Validate/reject/watchlist/more-research actions and analyst notes persist and create audit events.
- Authenticated analysts can save and replay named candidate-queue criteria and maintain multiple dedicated watchlists. Watchlists reference existing candidates rather than copying evidence; membership additions and removals are audited.
- Authenticated analysts can explicitly initiate a bounded 1–100 record refresh of the approved free Colorado and Texas sources. Each durable refresh records attribution, contract fingerprint, acquisition-run linkage, aggregate results, actual/approved cost, freshness limitations, and a safe failure code; Utah remains delivery-based and no scheduler is active.
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
- The approved Milestone 4.7 AI work made zero search calls and recorded $0.23 aggregate estimated provider cost. Six business extractions completed. The final subject-bound ambiguity contract retained two Utah proposals and one Texas non-owner proposal while deterministically rejecting both Colorado outputs and the Texas Claude output for unsupported ownership interpretation. Dave Jensen deferred Utah/OpenAI, accepted Utah/Claude, and corrected Texas/OpenAI's business status while retaining its non-owner conclusion. Only Utah entered the real `needs_review` queue; Issue #92 tracks the open-ended OpenAI result.
- Credential-free mode, frontend build/tests, backend/API tests, Compose configuration, and a full Nginx/FastAPI/PostgreSQL stack were exercised during reconciliation.

## Implemented but not fully validated

- OpenAI and Anthropic adapters support bounded summaries and schema-validated extraction behind a provider interface. Both processed the approved public-evidence cohort; the resulting evaluation failures are recorded rather than represented as validation.
- Alembic has an initial schema revision validated against an empty SQLite database.
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

Proceed to Milestone 5 Issue #98: gate opt-in analyst alerts on trustworthy refresh outcomes. Alert implementation must remain user-controlled and cannot convert refresh into unattended acquisition without a separate decision. Issue #92 remains a deferred OpenAI quality follow-up and does not authorize another paid run.

Repository documentation was reconciled in Issue #56 before beginning that version-two contract. `docs/README.md` now distinguishes living specifications from historical ADR, milestone, experiment, and validation records; the implementation and this file remain the final truth check when records disagree.

## Latest validation

The current implementation exercises 168 backend/API tests and five frontend tests. All seventeen migrations upgraded, downgraded, and re-upgraded on an empty SQLite database; the production frontend built with its existing large-chunk warning; Compose configuration validated; and a rebuilt PostgreSQL/FastAPI/Nginx stack became healthy, returned `/api/health`, and rendered the local dashboard. The bounded Utah delivery achieved 100% ingestion success across 188 entities, 188 BUSINFO rows, and 470 PRINCIPAL rows; all joins resolved without duplicate keys, orphan rows, or quarantine, and an identical repeat added no artifacts. The optional-provider API image builds with both SDKs. The version-two replacement and Milestone 4.1–4.4 contracts remain validated against fictional fixtures and adapter mocks. The Issue #71 run added three OpenAI web-search calls at a conservative estimated cost of $0.06, landed three immutable artifacts that failed exact-excerpt qualification, and made zero model-analysis calls.

Milestone 5 Issue #95 adds two backend tests for persisted score provenance and evidence-derived recalculation. All 168 backend tests passed, and migration 17 upgraded, downgraded to the prior head, and re-upgraded on a fresh SQLite database. This work made no live search or model calls and incurred $0 external spend.

Milestone 5 Issue #96 adds two backend workflow tests. All 170 backend tests and five frontend tests passed, the production frontend built with its existing large-chunk warning, and all eighteen migrations upgraded with migration 18 successfully downgraded and re-upgraded on a fresh SQLite database. The rebuilt local Compose stack became healthy, and rendered inspection confirmed both the dedicated Watchlists workspace and replayed Colorado/60% candidate filters. This work made no live search or model calls and incurred $0 external spend.

Milestone 5 Issue #97 adds three backend tests and one frontend presentation test. All 173 backend tests and six frontend tests passed, and the production frontend built with its existing large-chunk warning. Two explicitly approved five-record live refreshes then succeeded at $0: Colorado retrieved five records and curated ten subjects including five registered-agent assertions; Texas retrieved and curated five entity records. Both had zero quarantine and zero ownership-supported assertions. Both honestly reported that freshness is not measurable from individual records. No search or model calls occurred.

Milestone 4.7 closeout re-ran all 166 backend tests and five frontend tests, the production frontend build, Compose configuration, and all sixteen migrations through upgrade, downgrade, and re-upgrade on a fresh SQLite database. All passed; the existing frontend large-chunk warning remains. No closeout UI behavior changed, so the previously rendered application baseline remains applicable.

Milestone 2.2 previously validated the real Google browser flow, JIT identity, signed session, and user-linked audit attribution. Credentials remain in the ignored root `.env`; provider tokens are not persisted. Broader breakpoint coverage remains partial.
