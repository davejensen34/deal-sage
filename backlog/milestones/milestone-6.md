# Milestone 6 — Operational Productization

Status: proposed; gated by demonstrated pilot workflow value.

## Goal

Harden the single-box product for dependable multi-user pilot operation without prematurely introducing distributed infrastructure.

## Intended scope

- Organization and role boundaries beyond the current pilot identity.
- Backup, restore, retention, secret rotation, and operational runbooks.
- Production monitoring, health, audit review, and source/model cost visibility.
- Deployment hardening and safe upgrade/rollback procedures for the chosen hosting target.
- Performance work driven by observed limits, including PostgreSQL search features where justified.

## Boundary

Start with the existing portable web/API/database/storage architecture. Queues, Kubernetes, vector infrastructure, and other recurring-cost services require measured need and a separate architecture decision.
