# System-selected retained-evidence extraction

Issue #201 adds the first automatic retained-evidence stage for #194. One frozen authorization selects and executes multiple source passages without a human choosing each excerpt or approving each model call. This is a backend service/API increment; there is no new UI or worker. It does not discover new sources, reconcile identities, validate extraction semantics, create typed source claims, synthesize recommendations or finish M8.

## Selection and frozen scope

`retained-extraction-batch-v1` accepts a purpose-specific `TargetProfile` and call/cost/elapsed-time ceilings. Defaults are two calls, six cents and 300 seconds, subject to the existing stricter configured case limits; at most four calls and 900 seconds can be requested. A profile does not change provider/model/token limits or authorize a live evaluation by itself.

Preview reads at most the first twenty case evidence records in ID order through the hash-verified source-passage service. Every considered document gets readable coverage metadata or an unavailable/restricted outcome. Total and uninspected document counts remain visible. Passage selection uses deterministic lexical groups: transition cues, business context, requested industry/exclusions, employee/revenue clues and applicable company-type criteria. Each matching group contributes once; repeated words cannot inflate priority. Negated statements and excluded industries remain research clues. This priority is neither fit, truth nor recommendation confidence.

Higher-priority passages sort first, then evidence ID and passage index. Openings are context fallbacks when no cues match. Exact excerpt hashes are deduplicated within the batch; this is not syndication/independence analysis and does not deduplicate prior authorized batches. Coverage, duplicate counts and unselected passage counts remain in the frozen plan. No claim of comprehensive article coverage follows from selecting a few passages.

The plan freezes the profile, limits, provider policy, selected child packets/hashes and coverage. A stale preview cannot create an authorization. Each child admission rechecks the retained bytes and provider configuration through the existing extraction service. New evidence after authorization is outside the frozen batch; changing selected evidence/provider settings stops admission. Empty selection completes with zero calls and `readiness: not_assessed`, never a manufactured opportunity.

## Durable execution and accounting

`ExtractionBatch` stores the request identity, authorizing actor, immutable plan/hash, next step, status, lease and absolute deadline. Creation and every state transition are audited. User-linked parent authorization/start/recovery records preserve real operators. Children are attributed to the batch as automated work, not to a fabricated human decision.

Execution atomically claims a ready batch and processes its frozen steps serially. Child request UUIDs derive from the parent request UUID and step number; child identity is scoped to the batch. A second execute request observes the running state instead of launching another runner. Each child commits its existing durable reservation before provider I/O. The parent then checkpoints the retained result. Failed, invalid and unknown children consume slots and are not retried automatically; later selected steps can still run. Exhausting the selection means the batch completed its work, not that extraction quality passed.

The parent ceiling is an authorization limit, not another spend reservation. Reporting counts only linked child attempts and the larger of each reservation or measured estimate. Existing case-wide extraction limits include other model work and remain authoritative. If another action consumes capacity first, this batch stops rather than exceeding it. Concurrent batches on a case cannot bypass the child service's single-active-extraction guard. Another call is not admitted unless its full timeout fits inside the absolute batch deadline and its reservation fits the remaining batch ceiling. Already-incurred invalid/over-limit provider usage stays recorded.

Cancellation prevents further admissions. An already admitted call can finish and retain its proposal/cost; cancellation cannot reverse a provider request. The parent row is held through child reservation so cancellation cannot slip between the parent check and admission. No locks are held during provider I/O.

After the lease and child timeout/grace have elapsed, explicit recovery fences the old runner, preserves an interrupted child as unknown and returns the batch to ready. Resume replays existing child outcomes, including a result published just before a process failure, without another call. The original deadline is not extended, and no slot or reservation is refunded. A late child response cannot overwrite recovered history or advance the old runner. Recovery validates child identity and cannot mutate a conflicting standalone attempt.

## API and deployment

Authenticated readers may `POST /api/research/cases/{case_id}/extraction-batches/preview` with batch settings or read `GET .../{batch_id}`. Operators with `execute_ai` may create a batch by posting `{config, request_key, expected_hash}` to the collection, then invoke `POST .../{batch_id}/execute`, `/cancel` or `/recover`. Preview performs no external calls or database writes. Execution runs in the current request/process; the durable recovery contract precedes any future background worker. All reads/actions are case scoped.

Migration `d201a0b1d839` adds one table after `c178a0b1d838`. Downgrade refuses to discard retained batch history. Use migration-gated startup and the paired database/evidence [pilot recovery procedure](../deployment/pilot-recovery.md) before upgrading a real corpus. Only temporary test databases were migrated in this increment; the running acceptance app/corpus was not changed.

## Validation and next work

The 622-test backend/API suite passes. New tests exercise automatic later-context selection through a cited model proposal, explicit negative clues, stale plans, partial failure continuation, duplicate execution, cancellation, checkpoint interruption, multi-session recovery/late-response fencing, child identity conflicts, actual-versus-reserved cost accounting, elapsed/case limits, inventory bounds, operator permissions, migration/reopen and downgrade refusal. All provider/source data is fictional or injected; no live source/model calls ran.

The current lexical selector is a bounded baseline, not intelligent synthesis or a measured quality improvement. Next #194 stages must add semantic reconciliation, material-uncertainty-driven corroborating searches under a shared allowance, cited assessments and recommendation delivery, then end-to-end evaluation. Human acceptance #187 remains paused; the original ten-record corpus and failed observations remain intact.
