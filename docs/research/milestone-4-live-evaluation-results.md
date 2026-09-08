# Milestone 4 governed live evaluation result

Protocol `m4-e2e-v1-2026-09-08` was explicitly approved and executed on September 8, 2026. The run stopped without sending evidence to either model provider because the frozen source packet did not reproduce. This is a negative integration result, not a model-quality result.

## Approved and observed bounds

| Measure | Approved ceiling | Observed |
| --- | ---: | ---: |
| Cases | 3 | 3 discovery searches started before the runner defect was identified |
| Live calls | 18 | 3 OpenAI web-search calls; 0 model-analysis calls |
| Estimated spend | $2.00 | $0.06 conservative estimate |
| Model input/output tokens | 12,000/4,000 per case | 0/0 |

The ignored manifest hash was `e1a6a4247d421d044ceaab79ba7e354bc85f81da3e6d80c3985e71bba36858a9`. OpenAI `gpt-5-mini`, Anthropic `claude-sonnet-4-5`, the three state/origin slots, and the approved ceilings matched the frozen protocol. No credentials or raw evidence are included in this record.

## What happened

- Search returned 15 candidates across Colorado, Utah, and Texas. Search snippets remained untrusted candidates and were never promoted to evidence.
- Three of six frozen source URLs returned an HTTP failure during ordinary retrieval.
- The other three URLs landed as immutable artifacts, but their current page text did not contain the exact prequalified excerpts. They therefore failed evidence qualification and were not supplied to a model.
- No model proposal was created, so there was no provider output to accept, correct, reject, or defer. The human pre-labels were not changed.
- The initial runner continued the remaining discovery searches after the first qualified-source failure. That violated the intended immediate-stop behavior even though it exposed no evidence to a model and remained within the approved call and cost ceilings. The runner now preserves the partial case and stops before another case or model call on a frozen-source failure.
- Changing an excerpt, replacing a source, or rerunning under the same protocol after observing live output would violate the frozen-manifest rule. The remaining 15-call and $1.94 budgets were therefore left unused.

## Decision

This protocol did not meet the passing criteria: all three cases lacked a reproducible qualified evidence packet, no case reached an analyst-reviewed model disposition, and no live version-two model-quality conclusion is possible. Issue #71 should close as an honestly stopped evaluation rather than as a quality validation.

Milestone 4 may proceed to its explicit closeout path because its definition of done permits recording a governed stop. Milestone 5 must not treat this run as evidence that live model output is adequate. A future live evaluation requires a new protocol ID and approval. Its preflight should retrieve and hash every frozen source, capture an excerpt from the landed artifact, and validate the complete packet before the first paid search or model call.
