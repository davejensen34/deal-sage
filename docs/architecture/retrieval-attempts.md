# Explicit document retrieval

Issue #164 extends the 8.3 case investigation panel. An operator explicitly authorizes one document from a source with an attributable approved access decision. Pending/blocked decisions, known access restrictions, stopped cases and changed URLs fail before I/O. Source evidence remains unverified content; retrieving it creates no claims, model output, ownership finding, human conclusion or downstream promotion.

## Frozen authorization

`RetrievalAttempt` stores the UUID request key, case/source, actor, `case-document-v1` policy, exact source URL/provider, status, recovery deadline, safe error code and evidence ID. Limits are one document, 1,000,000 bytes, 20 seconds, zero redirects, zero automatic retries, three total attempts per source and twenty per case. Failures/unknown outcomes consume attempt capacity. The public HTTP provider has no source/API fee; model calls are zero. These pilot limits are deliberately fixed for this increment and are not editable workspace defaults.

Admission locks the case row briefly, verifies its open state and remaining capacity, then commits the authorization and user-linked audit before any external call. Only one active retrieval is admitted per case. Reusing a key returns the saved outcome; reuse for another case/source/URL/actor is rejected. A browser transport retry keeps the original key. The initial discovery document budget stays frozen at zero: the separately reviewed source action supplies a durable one-document authorization rather than mutating the discovery plan.

Demo mode never retrieves real URLs. Its fixture additionally requires demo authentication and `example.test/fictional-discovery/…`; it returns explicitly fictional text and cannot attach fictional evidence to a real source URL. Non-demo execution uses `HttpDocumentProvider` with existing public-address, size and media defenses and redirects disabled. Publisher access conditions still require review before approval. No credentials editor, login bypass or automatic retry is introduced.

## Atomic publication and recovery

`CandidateRetrievalService` reuses existing content-addressed `EvidenceLanding` and `ResearchCaseService`. Their new deferred-commit option permits the outer attempt transaction to commit artifact/acquisition rows, evidence linkage and success together. Legacy callers retain their original commit behavior. Raw bytes are saved before SQL publication; a storage/SQL failure can leave unreferenced content-addressed bytes, but cannot publish evidence or a successful outcome. Filesystem writes are not claimed to be transactional. Normal paired database/evidence backups retain the recovery boundary.

After network I/O, a conditional update locks the still-running attempt through SQL landing. A recovered attempt cannot publish a late response. A provider response beyond the deadline is rejected even if its coroutine ignores cancellation. Failure rolls back SQL landing and retains only a safe outcome class. Same-content evidence remains deduplicated under the existing artifact contract.

Process interruption leaves a durable running attempt. After the 20-second timeout plus a 60-second grace period, explicit operator recovery marks it unknown and records attribution without another request. Recovery that races with publication uses the same row lock. A subsequent retrieval requires a new explicit action within remaining capacity; unknown outcomes and prior keys are retained. No scheduler or distributed queue is introduced.

## Deployment and remaining work

Apply migration `d164a0b1d833` after `c158a0b1d832`. Downgrade refuses to discard any retrieval history. Follow [pilot recovery](../deployment/pilot-recovery.md) before changing the real corpus. This increment migrated only the fictional local validation database and made no live requests.

Tests cover zero-discovery-budget authorization, same-key replay, duplicate evidence, failed attempt caps, concurrent admission, recovery/late-response fencing, SQL rollback after evidence failure, operator/source boundaries, demo URL restrictions, migration/reopen and downgrade refusal. Rendered validation exercised fictional discovery, access approval, retrieval, excerpt/artifact inspection and reload, plus the narrow layout. Existing HTTP contract tests remain part of the full suite.

8.3 remains active for extraction, frontier execution, explicit independence inspection and versioned case insight updates. Retained documents alone do not complete the 8.1→8.3 insight journey or any live human quality gate.
