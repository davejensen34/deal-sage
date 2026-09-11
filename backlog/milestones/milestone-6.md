# Milestone 6 — Operational Productization

Status: complete as of September 11, 2026. Explicitly approved after Milestone 5.1 demonstrated pilot workflow value and exposed a real upgrade gap.

## Goal

Harden the single-box product for dependable multi-user pilot operation without prematurely introducing distributed infrastructure.

## Workstreams

- #114 makes database upgrades explicit and safe for empty, versioned, and recognized legacy deployments (merged in PR #120).
- #115 enforces viewer/analyst/operator/administrator permissions, audited denials, explicit user lifecycle changes, and same-origin mutation protection (merged in PR #121).
- #116 proves database/evidence backup and separate-target restore, then records retention/deletion, RPO/RTO, secret rotation, access recovery, and release rollback boundaries (merged in PR #122).
- #117 separates liveness/readiness and exposes role-limited, aggregate-safe schema, storage, audit, failure, source/model health, and cost visibility (merged in PR #123).
- #118 removes insecure pilot defaults, hardens proxy/headers/dependency health, boots the full stack in CI, records bounded vulnerability checks, and establishes a measured performance baseline (merged in PR #124).
- #119 reconciles validation and closes the milestone (this closing record).

## Definition of done

- Application traffic cannot begin against a failed or stale schema, and the existing unversioned local volume has a data-preserving adoption path.
- Privileged actions are authorized server-side and denials remain auditable.
- A separate restore target reproduces database/evidence integrity from documented backups.
- Operators can distinguish liveness, readiness, degraded dependencies, recent failures, cost, and audit coverage without seeing retained source content.
- Hardening and indexes respond to measured limits rather than speculative scale.
- Repository and GitHub product records match observed validation and external spend.

## Boundary

Start with the existing portable web/API/database/storage architecture. Queues, Kubernetes, vector infrastructure, and other recurring-cost services require measured need and a separate architecture decision.

## Result

Milestone 6 converted the proven local product into a substantially safer single-host pilot without changing its evidence, inference, or human-review boundaries. Schema changes are migration-gated and adopt only recognized legacy shapes. Pilot identities are least-privilege by default, privileged actions are server-authorized, and denials and lifecycle changes are auditable. Database and evidence backups are coupled and verified in an isolated restore target. Operators can distinguish liveness from aggregate dependency readiness without exposing retained research content. Pilot configuration fails closed, proxy and browser boundaries are explicit, and health-aware startup survives API recreation.

The milestone deliberately did not add scheduling, distributed workers, Kubernetes, caches, vector storage, external monitoring, or managed backup transport. Recovery transport and production monitoring remain operator responsibilities; the current audit-write failure counter remains process-local; source coverage and beneficial-ownership truth remain product risks rather than operational claims.

## Validation

- PRs #120–#124 merged for Issues #114–#118; Issue #119 owns this closeout.
- 209 backend/API tests and ten frontend tests passed. The production frontend built with its existing large-chunk warning.
- Twenty-one migrations were exercised through empty, versioned, and recognized legacy paths; the historical PostgreSQL volume was backed up and adopted without losing its existing user.
- A coupled database/evidence backup restored into disposable isolated volumes at the expected schema revision with archive-hash verification.
- The full PostgreSQL → migration → API → Nginx stack passed locally and in CI. Nginx retained connectivity after API recreation and served the expected security headers.
- Python, production npm, API-image, and web-image vulnerability gates passed. The initial web scan's fixed Alpine findings were resolved by upgrading the runtime; none was waived.
- Representative in-process maxima were 16.5 ms queue, 29.0 ms detail, 3.6 ms research aggregate, 8.5 ms export, and 9.8 ms fixture refresh, all within their documented pilot regression budgets.
- No live source, search, identity-provider, or model calls were made during Milestone 6; external spend was $0.

No milestone is active after this closeout. Milestone 7 remains proposed and requires explicit approval.
