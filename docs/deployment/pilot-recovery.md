# Pilot backup and recovery

DealSage's single-host pilot has two coupled durable stores: PostgreSQL metadata and the evidence volume. A valid backup contains both, a versioned manifest, and SHA-256 hashes. It excludes `.env`, provider credentials, session secrets, logs, and source files retained outside the evidence volume.

## Objectives

- Recovery point objective (RPO): at most 24 hours of accepted pilot work.
- Recovery time objective (RTO): restore service within four hours of declaring a recoverable host or release failure.
- Create a daily operator backup before the first work session and immediately before upgrades or material data operations. This is an operator procedure, not an in-app scheduler or recurring-cost service.
- Retain seven daily and four weekly validated backups. Store at least one encrypted copy away from the application host. Delete expired copies from every location and record the operator action outside the backup bundle.

## Create a consistent backup

From the repository root, choose a destination outside the repository when possible:

```bash
./scripts/pilot-backup.sh /secure/path/dealsage-backup-YYYY-MM-DD
```

The script briefly stops the API—the pilot's only writer—then captures a custom-format PostgreSQL dump and the evidence volume. It restarts the API and reverse proxy on success or failure and writes `manifest.json` with the Alembic revision and both archive hashes. A newly created manifest deliberately says `validated_restore: false`; archive creation alone is not recovery proof.

## Restore and verify in isolation

```bash
./scripts/pilot-restore-verify.sh /secure/path/dealsage-backup-YYYY-MM-DD
```

This refuses changed archive hashes, creates a separate `dealsage-restore-check` Compose project and volumes, restores both stores, confirms the restored schema revision, then verifies that every `raw_artifacts.storage_key` exists with the recorded byte size and SHA-256 hash. The isolated stack is removed afterward. A successful run writes a separate `restore-verification.json` bound to the manifest hash; the original manifest stays immutable.

For disaster recovery, first run this isolated verification, stop the affected stack, preserve its volumes until the recovery is accepted, and restore the verified bundle into newly created production volumes. Never restore over the only remaining copy.

## Release recovery

Prefer rolling the application image back only when the earlier image is forward-compatible with the current schema. Alembic migrations are not assumed to be safely reversible. If compatibility cannot be established, restore a separately verified pre-release backup into new volumes and point the selected application release at them. Compare its schema revision and integrity report before reopening writes.

## Retention and deletion

| Record | Pilot policy |
| --- | --- |
| Raw evidence and lineage | Retain while a case, decision, audit, or source contract depends on it. Delete only through a future lineage-aware product workflow; manual volume deletion is prohibited. |
| Model proposals and dispositions | Retain with the case and cited evidence. Provider-side response storage remains disabled. |
| Audit history | Retain for the pilot. It is part of the accountability record and is not a secrets store. |
| Deactivated users | Retain the stable identity key, status, role history, and audit attribution; do not hard-delete while referenced. |
| Backups | Seven daily plus four weekly validated copies, then securely delete. A legal, source-contract, or incident hold overrides expiry. |

Raw evidence may contain personal data. A future deletion feature must resolve candidate, claim, proposal, decision, and audit dependencies and record what was removed; filesystem deletion alone would destroy provenance while leaving misleading database references.

## Secret and access recovery

Secrets are supplied through environment configuration and are never backed up by these scripts. After suspected disclosure, revoke/rotate the Google OAuth secret and any OpenAI or Anthropic keys at their providers, replace `SESSION_SECRET` (invalidating sessions), update the host's protected `.env`, restart the stack, and confirm login plus disabled-by-default provider settings. Review authorization-denial and access-change audits; provider portals remain the source of truth for key activity.

Keep at least two named pilot administrators. If ordinary access is lost but host access remains, use the audited local command in `pilot-authentication.md` to reactivate or promote a known allowlisted identity. If host access is lost, recover the host through its operating-system/cloud access process, restore a verified backup, rotate all secrets, and then recover the DealSage administrator. DealSage does not embed a bypass account or recovery credential.

## Milestone 7 relationship activity upgrade

Revision `a729e10b3c42` permits unknown (`NULL`) current relationship activity while preserving every existing true/false value. Use the normal coupled backup and isolated restore procedure before upgrading the pilot. Empty and versioned stores upgrade through Alembic; recognized unversioned stores also receive this nullability change before stamping. A downgrade refuses to proceed while unknown values exist rather than replacing uncertainty with invented facts. The Windows validation used a separate fictional SQLite store; it does not replace PostgreSQL/evidence recovery verification.
