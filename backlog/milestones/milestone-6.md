# Milestone 6 — Operational Productization

Status: active as of September 10, 2026. Explicitly approved after Milestone 5.1 demonstrated pilot workflow value and exposed a real upgrade gap.

## Goal

Harden the single-box product for dependable multi-user pilot operation without prematurely introducing distributed infrastructure.

## Workstreams

- #114 makes database upgrades explicit and safe for empty, versioned, and recognized legacy deployments (merged in PR #120).
- #115 enforces viewer/analyst/operator/administrator permissions, audited denials, explicit user lifecycle changes, and same-origin mutation protection (implemented and validated; PR pending).
- #116 proves database/evidence backup and separate-target restore, then records retention/deletion, RPO/RTO, secret rotation, access recovery, and release rollback boundaries.
- #117 separates liveness/readiness and exposes role-limited, aggregate-safe schema, storage, audit, failure, source/model health, and cost visibility.
- #118 removes insecure pilot defaults, hardens proxy/headers/dependency health, boots the full stack in CI, records bounded vulnerability checks, and establishes a measured performance baseline.
- #119 reconciles validation and closes the milestone.

## Definition of done

- Application traffic cannot begin against a failed or stale schema, and the existing unversioned local volume has a data-preserving adoption path.
- Privileged actions are authorized server-side and denials remain auditable.
- A separate restore target reproduces database/evidence integrity from documented backups.
- Operators can distinguish liveness, readiness, degraded dependencies, recent failures, cost, and audit coverage without seeing retained source content.
- Hardening and indexes respond to measured limits rather than speculative scale.
- Repository and GitHub product records match observed validation and external spend.

## Boundary

Start with the existing portable web/API/database/storage architecture. Queues, Kubernetes, vector infrastructure, and other recurring-cost services require measured need and a separate architecture decision.
