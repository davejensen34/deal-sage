# Milestone 5.1 — Workflow Traceability and Effectiveness

Status: active as of September 10, 2026. This follow-up preserves Milestone 5's historical closure while completing two gaps found in its post-close audit.

## Goal

Make refresh alerts self-resolving and make the value and limitations of source-to-review workflows measurable without inventing lineage.

## Workstreams

- #107 preserves refresh, acquisition, freshness, failure, and aggregate-safe quarantine context in alerts (implemented and validated; PR pending).
- #108 adds deterministic source-to-disposition effectiveness measures with explicit unattributed counts.
- #110 reconciles validation and closes the follow-up.

## Definition of done

- An alert remains understandable without relying on a truncated refresh-history list.
- Quarantine alerts identify stable internal curated-record references but expose no retained record content.
- Analysts can see source coverage, freshness, cost, candidate/review outcomes, and honest attribution gaps.
- Metrics never infer a source-to-candidate relationship that is absent from durable data.
- API and rendered UI behavior are validated, repository product records are reconciled, and external spend is reported.

## Boundary

This milestone adds observability over existing manual workflows. It does not authorize autonomous acquisition, scheduled refresh, external notifications, new paid calls, or probabilistic source attribution.
