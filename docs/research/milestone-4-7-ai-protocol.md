# Milestone 4.7 governed AI-to-review protocol

Status: proposed. This document and configured credentials do not authorize provider calls or spending.

## Approval requested

- Protocol ID: `m4-7-ai-v1-2026-09-09`
- Frozen packet file hash: `a8d535ed00ade57f3775dd9ad13bcc9b2f48998b077035d1922aa223ebbf84f9`
- Cases: the three preflighted Colorado, Utah, and Texas cases; no replacement after approval
- Providers/models: OpenAI `gpt-5-mini` and Anthropic `claude-sonnet-4-5`
- Tasks: business extraction and ambiguity analysis for each provider and case
- Search calls: zero; all six evidence documents are already landed locally
- Maximum model calls: 12, exactly four possible calls per case; no retry may exceed this ceiling
- Maximum estimated cost: USD $1.00 total, with $0.25 per case and a $0.25 unspendable reserve after the third case
- Provider order: OpenAI first for Colorado and Texas; Anthropic first for Utah
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

Passing integration requires all twelve executions to remain within the approved bounds, every completed observation to cite only the frozen case evidence, no unsupported owner promotion, and every proposal to receive human disposition. Quality reporting remains per dimension and must preserve abstentions and negative outcomes.

Pricing references checked September 8, 2026:

- [OpenAI GPT-5 mini](https://developers.openai.com/api/docs/models/gpt-5-mini)
- [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing)
