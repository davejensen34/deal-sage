# Milestone 4.7 governed AI-to-review protocol

Status: executed with governed corrective supplements on September 9, 2026. Human disposition remains pending.

## Final approved bounds

- Final protocol ID: `m4-7-ai-v4-2026-09-09`
- Frozen packet file hash: `a8d535ed00ade57f3775dd9ad13bcc9b2f48998b077035d1922aa223ebbf84f9`
- Cases: the three preflighted Colorado, Utah, and Texas cases; no replacement after approval
- Providers/models: OpenAI `gpt-5-mini` and Anthropic `claude-sonnet-4-5`
- Tasks: final ambiguity analysis for each provider and case; earlier bounded stages completed the business-extraction matrix
- Search calls: zero; all six evidence documents are already landed locally
- Maximum model calls: six final ambiguity calls; corrective protocols remained separately bounded and preserved
- Maximum estimated cost: USD $0.75 for the final protocol, with $0.25 per case
- Output ceiling: 3,000 tokens for the final ambiguity comparison
- Model input: only the two exact verified excerpts and deterministic source claims for that case
- Output: immutable, non-authoritative proposals; no candidate is validated or scored by a model

The ceiling is intentionally conservative. At the frozen September 8 rates, OpenAI GPT-5 mini is $0.25 per million input tokens and $2.00 per million output tokens; Anthropic Claude Sonnet 4.5 is $3.00 and $15.00 respectively. DealSage rounds any non-zero call estimate up to one cent. Official prices and configured model IDs must be checked again immediately before execution; abort rather than substitute.

## Human pre-labels

| Slot | Expected interpretation | Expected disposition |
| --- | --- | --- |
| M47-CO-1 | Identity resolved; founder/chairman role at the transition, but the packet does not prove ownership; active successor is explicit | no qualifying ownership relationship / more research if the model abstains on role |
| M47-UT-1 | Identity and explicit owner relationship at the transition are supported; the national business remains active, while local succession is unknown | candidate supported for analyst review, never automatically validated |
| M47-TX-1 | Identity resolved; principal ownership ended before the later transition and the business remains active under a successor | no qualifying relationship, with timeline contradiction resolved |

The machine-readable ignored manifest freezes the seven version-two dimensions and the two evidence IDs for each case before execution.

## Execution and stop rules

1. Validate this exact protocol, packet hash, models, tasks, cases, and ceilings before constructing a provider.
2. Re-verify each local artifact hash; do not refetch or substitute evidence.
3. Create explicit source claims from the verified excerpts. A role claim retains its exact semantics; founder, chairman, or senior chair never becomes owner.
4. Run the two tasks against identical evidence and claims for both providers.
5. Apply schema, citation, identity-support, relationship-time, owner-role, call, token, and cost validation deterministically.
6. Persist completed, invalid, refusal, incomplete, or failed executions without unsafe provider payloads.
7. Present every proposal for attributable human accept/correct/reject/defer disposition. Do not create a validated opportunity before that review.
8. Stop immediately on packet drift, unapproved input, missing lineage, budget projection, provider/model mismatch, or absent audit data. Do not silently retry.

Passing integration requires the final six ambiguity executions to remain within their approved bounds, every completed observation to cite only frozen case evidence, no unsupported or cross-subject owner promotion, and every reviewable proposal to receive human disposition. Quality reporting remains per dimension and must preserve abstentions and negative outcomes.

## Execution record

The first authorized protocol (`m4-7-ai-v1-2026-09-09`) made twelve request attempts that both APIs rejected before token usage because the constrained-output schema included unsupported validation keywords. Recorded cost was $0.00. The provider error class was retained while response bodies were not.

Protocol v2 moved those constraints to deterministic post-validation and ran the full twelve-call matrix for $0.12. Claude completed six of six; OpenAI completed one of six and explicitly recorded five incomplete executions at the 1,000-token output cap. Protocol v3 ran only those five missing OpenAI tasks at a 3,000-token cap; all completed for $0.05.

Human review then found that the ambiguity contract could cite one person's owner claim while characterizing another person's relationship. Protocol v4 therefore requires the transition subject explicitly and requires current- or former-owner output to cite an owner claim for that same person. Its six ambiguity calls cost $0.06: three passed deterministic validation and three unsupported owner interpretations were retained as invalid without provider output.

Across all protocol stages, 35 request attempts cost an estimated $0.23 and made zero search calls. The intended business-extraction matrix has six completed outputs. Under the final ambiguity contract, two Utah outputs and one Texas non-owner output were reviewable; both Colorado outputs and the Texas Claude output were rejected. Dave Jensen deferred Utah/OpenAI proposal #32, accepted Utah/Claude proposal #33, and corrected Texas/OpenAI proposal #34 from inactive to active while retaining its non-owner conclusion. Only the accepted Utah case entered the `needs_review` queue; its unresolved legal entity, successor, and current local operation remain explicit. Issue #92 tracks the deferred OpenAI ambiguity.

Pricing references checked September 8, 2026:

- [OpenAI GPT-5 mini](https://developers.openai.com/api/docs/models/gpt-5-mini)
- [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing)
