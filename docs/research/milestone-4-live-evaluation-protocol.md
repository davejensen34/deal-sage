# Milestone 4 governed end-to-end quality evaluation

Status: approved and stopped on September 8, 2026. The durable result is in `docs/research/milestone-4-live-evaluation-results.md`; this protocol does not authorize a retry.

## Decision to approve

Approve or revise this exact protocol before case qualification makes a provider call:

- Protocol ID: `m4-e2e-v1-2026-09-08`
- Cohort: three retrospective public cases, one each in Colorado, Utah, and Texas
- Origins: one signal-first, one business-first, and one hybrid conflict or non-resolution case
- Model providers: OpenAI and Anthropic
- Models: `gpt-5-mini` and `claude-sonnet-4-5`
- Search provider: OpenAI web search, used only for candidate discovery; ordinary direct retrieval remains preferred once a source URL is known
- Maximum live calls: 18 total — at most six search calls and twelve model-analysis calls
- Maximum spend: USD $2.00 total, with a $0.50 ceiling per case and a $0.50 reserve that cannot be spent after the third case
- Execution order: case-by-case, alternating which model provider runs first
- Stop policy: stop immediately on any safety, access, provenance, schema, budget, or protocol-integrity failure

The selected models preserve continuity with the adapters and earlier connectivity exercise. Official pricing must be checked again immediately before approval and execution. As of protocol drafting, OpenAI lists `gpt-5-mini` at $0.25 per million input tokens and $2.00 per million output tokens, while Anthropic lists Claude Sonnet 4.5 at $3.00 and $15.00 respectively. Search-tool charges are additional, so the call counter and total-dollar ceiling are independent hard stops.

## Cohort contract

The three slots are fixed before subjects are chosen:

| Slot | State | Origin | Pre-labeled condition | Required evidence |
| --- | --- | --- | --- | --- |
| M4-CO-1 | Colorado | signal first | A public transition signal names or strongly identifies a person; research must determine whether a current qualifying business relationship can be supported | transition source, authoritative entity anchor, and independent relationship or operating-status source |
| M4-UT-1 | Utah | business first | A bounded business source exposes a person-role candidate; research must determine whether a transition signal and current qualifying relationship converge | Utah entity/role evidence plus independent transition and current-operation evidence |
| M4-TX-1 | Texas | hybrid | Sources conflict, remain ambiguous, or support a negative outcome | at least two independent sources that make the conflict or non-resolution explicit |

Cases must be retrospective, publicly documented, and selected without model assistance. Qualification records only URLs and short notes in an ignored local manifest. Do not collect private contact details, research living relatives beyond an explicit business relationship, contact any subject, or publish a lead list. Stop at authentication, paywalls, CAPTCHAs, robots restrictions, access prohibitions, or unclear reuse terms.

The human pre-label uses the seven version-two dimensions before any provider output is seen. A replacement must preserve the same state, origin, and expected-condition slot, and its reason must be recorded before execution.

## Per-case ceilings

- Two search calls, each returning no more than five candidates.
- Six source documents opened, with no more than five persisted evidence items.
- Two model tasks per provider: structured extraction and ambiguity analysis. No separate model-authored conclusion is allowed.
- Four total model calls; one retry may replace a transient failed call but cannot increase this ceiling.
- 12,000 total model input tokens and 4,000 total model output tokens across both providers.
- $0.50 estimated combined search and model cost.
- 20 minutes elapsed research time.
- One analyst disposition for every completed or non-completed proposal before moving to the next case.

Ceilings are limits, not targets. Existing case-level research budgets may be stricter and always win.

## Execution sequence

1. Validate the ignored manifest against the committed protocol and record its content hash.
2. Recheck official pricing and account model availability. Abort rather than substitute a model or raise a ceiling.
3. Capture the human pre-label and the initial public signal or business anchor.
4. Run bounded discovery. Search candidates remain untrusted and cannot be cited as evidence.
5. Apply source-access policy, retrieve approved documents, and land immutable artifacts before extraction.
6. Run the identical evidence packet through both model providers in alternating order.
7. Apply deterministic schema, citation, identity, role, timeline, contradiction, and budget validation.
8. Have the authenticated analyst accept, correct, reject, or defer every proposal with rationale.
9. Stop the case on convergence, non-resolution, conflict review, source denial, or any exhausted ceiling.
10. Publish only case IDs, aggregate-safe measures, negative results, and the proceed/change/stop recommendation.

## Measures

Report each case and aggregate totals for:

- candidate-source yield, permission denials, retrieval success, duplicate suppression, and landed-evidence lineage;
- schema-valid completion, citation validity, unsupported claims, identity/relationship/timeline and operating-status correctness against the frozen pre-label;
- contradiction detection, appropriate abstention or non-resolution, and analyst accept/correct/reject/defer outcomes;
- approved versus rejected research actions, convergence/stop reason, and reproducibility of deterministic transitions;
- calls, input/output tokens, latency, estimated provider cost, total cost, and unused budget.

This cohort can validate safe integration and expose failure modes. Three cases cannot establish market coverage, statistical model superiority, beneficial ownership, or production readiness.

## Passing and stopping decision

Milestone 4 may proceed to closeout only if all three cases preserve artifact and claim lineage, no unsupported citation is accepted, no name-only or registered-agent relationship is promoted, every proposal receives a human disposition, and every call stays within the frozen protocol. At least two cases must reach their correct pre-labeled disposition; the conflict/non-resolution case must not become a supported opportunity.

Stop the run immediately if any provider receives unapproved evidence, a search snippet becomes evidence, a source restriction is bypassed, the manifest changes after output is observed, a model mutates authoritative state, a required audit record is absent, or projected spend would exceed a ceiling. Preserve the partial result as negative evidence; do not silently retry or replace the case.

## Approval record

The user explicitly approved protocol `m4-e2e-v1-2026-09-08`, the named OpenAI and Anthropic models, the three-case cohort, 18-call ceiling, and USD $2.00 ceiling on September 8, 2026. Execution used three search calls and stopped before model analysis when the frozen evidence packet could not be reproduced. The approval is consumed and does not extend to a changed manifest or another run.

Pricing references checked September 8, 2026:

- [OpenAI GPT-5 mini model and pricing](https://developers.openai.com/api/docs/models/gpt-5-mini)
- [Anthropic model pricing](https://platform.claude.com/docs/en/about-claude/pricing)
