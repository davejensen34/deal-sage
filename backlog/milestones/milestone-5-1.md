# Milestone 5.1 — Workflow Traceability and Effectiveness

Status: complete as of September 10, 2026. This follow-up preserves Milestone 5's historical closure while completing two gaps found in its post-close audit.

## Goal

Make refresh alerts self-resolving and make the value and limitations of source-to-review workflows measurable without inventing lineage.

## Workstreams

- #107 preserves refresh, acquisition, freshness, failure, and aggregate-safe quarantine context in alerts (merged in PR #111).
- #108 adds deterministic source-to-disposition effectiveness measures with explicit unattributed counts (merged in PR #112).
- #110 reconciles validation and closes the follow-up (this closeout).

## Definition of done

- An alert remains understandable without relying on a truncated refresh-history list.
- Quarantine alerts identify stable internal curated-record references but expose no retained record content.
- Analysts can see source coverage, freshness, cost, candidate/review outcomes, and honest attribution gaps.
- Metrics never infer a source-to-candidate relationship that is absent from durable data.
- API and rendered UI behavior are validated, repository product records are reconciled, and external spend is reported.

## Boundary

This milestone adds observability over existing manual workflows. It does not authorize autonomous acquisition, scheduled refresh, external notifications, new paid calls, or probabilistic source attribution.

## Result

Complete. Refresh alerts retain enough durable aggregate context to resolve the triggering source refresh directly, including freshness, safe failure, acquisition-run, and quarantine references. The Research workspace now measures source landing, refresh cost and freshness, candidate lineage, and analyst dispositions without attributing unlinked candidates.

Validation against the existing local PostgreSQL volume exposed a deployment concern rather than a Milestone 5.1 correctness gap: that volume predates the evidence-lineage migration. The API and UI detect and disclose the missing capability and perform no candidate attribution. Applying migrations safely to deployed databases is proposed Milestone 6 work.

## Validation

- 182 backend tests and eight frontend tests passed.
- The production frontend build passed with the existing large-chunk warning.
- GitHub backend, frontend, and Compose checks passed for PRs #111 and #112.
- A rebuilt PostgreSQL/FastAPI/Nginx stack returned the effectiveness aggregate, and rendered inspection confirmed the alert context and effectiveness presentation.
- No live source, search, or model calls occurred; external spend was $0.
