# Milestone 6 — Operational Productization

Status: active as of September 10, 2026. Explicitly approved after Milestone 5.1 demonstrated pilot workflow value and exposed a real upgrade gap.

## Goal

Harden the single-box product for dependable multi-user pilot operation without prematurely introducing distributed infrastructure.

## Workstreams

- #114 makes database upgrades explicit and safe for empty, versioned, and recognized legacy deployments (implemented and validated; PR pending).
- #115 enforces a minimal single-organization pilot role model at privileged API boundaries.
- #116 proves database and evidence backup/restore procedures and retention guidance.
- #117 exposes aggregate-safe schema, storage, audit, source/model health, and cost visibility.
- #118 establishes a measured single-host deployment and performance baseline.
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
