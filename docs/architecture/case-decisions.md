# Reviewer workflow decisions

Issue #174 is the first Milestone 8.4 increment. A reviewer records `more_research`, `monitor` or `dismiss` for acquisition exploration, marketing introduction or succession advisory. These are human workflow intentions, separate from source claims, model dispositions, `AnalystConclusion` evidence judgments and candidate status. Monitoring intent schedules nothing; dismissal does not stop research execution. Development-brief creation/contact readiness/export follows separately.

## Version and correction contract

A decision references one immutable saved brief in the same case. The reviewer supplies rationale, next action, purpose and optional supporting/contradicting source IDs from that exact version. Empty evidence remains permissible for an explicitly explained lack-of-evidence decision. A source cannot occupy both selections; mixed evidence belongs in the rationale. Membership validates provenance, not source truth or ownership. Later evidence does not silently move a decision to a newer brief.

`CaseDecision` retains content, actor, stable actor key, brief ID, request UUID and prior decision ID. Recording a replacement requires the latest decision ID and a change reason. A case-row write serializes the chain, including its first row. Stale submissions conflict; identical actor/case/payload/request retries return the original committed result even after a later correction. Previous decisions remain unchanged. Decision and audit commit together, without source/model calls, candidate promotion or research-state mutation. Stopped cases may still receive human review.

Authenticated `GET /api/research/cases/{id}/decisions?page=1` provides the latest decision and ten history entries per page. `POST` requires review permission. There is no update/delete endpoint. Migration `b174a0b1d837` follows the follow-up migration and refuses a downgrade that would discard retained decisions. This is the existing single-organization authorization boundary, not tenant isolation.

## UI and observed validation

Case pages show the current decision and history. Reviewers load a specific saved brief version, inspect its retained source excerpts, select references and submit the decision. Loading a brief refreshes the current decision to recover from a conflict. A lost response retries the same payload/UUID. Viewers have read access only. The saved brief remains unchanged; workflow history is linked alongside it rather than copied back into that snapshot. Existing inbox filters and monitoring schedules are unchanged.

All 535 backend/API tests passed. All 46 frontend tests, TypeScript and the production build passed (existing chunk warning). Tests cover exact source/version membership, unsupported/mixed selections, no research-state mutation, correction history, stale submissions, actor-safe request replay, permissions, pagination and migration/reopen/downgrade protection.

The isolated fictional demo recorded more research against brief version 1, then replaced it with monitor and an explicit reason. Both decisions, author, source selections and next actions survived reload. Desktop and 390px layouts were inspected. Only the isolated demo received the migration; no live calls or operational-corpus changes ran. This does not complete 8.4 or the actual human usefulness gate.
